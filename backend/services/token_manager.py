# services/token_manager.py

import time
import requests
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models import StravaToken as ORMStravaToken
from backend.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET

def save_tokens(user_id: str, tokens: dict) -> None:
    """
    Insert or update the Strava tokens for a given user.
    """
    expires_at = tokens.get("expires_at", int(time.time()) + 2100)
    db: Session = SessionLocal()
    try:
        # Try to load an existing row
        orm_token = db.get(ORMStravaToken, user_id)
        if not orm_token:
            orm_token = ORMStravaToken(
                user_id=user_id,
                access_token=tokens.get("access_token"),
                refresh_token=tokens.get("refresh_token"),
                expires_at=expires_at,
            )
            db.add(orm_token)
        else:
            orm_token.access_token  = tokens.get("access_token")
            orm_token.refresh_token = tokens.get("refresh_token")
            orm_token.expires_at    = expires_at

        db.commit()
    finally:
        db.close()

def get_access_token(user_id: str) -> str | None:
    """
    Return a valid access token for the user, refreshing it if expired.
    """
    db: Session = SessionLocal()
    try:
        orm_token = db.get(ORMStravaToken, user_id)
        if not orm_token:
            return None

        if time.time() > orm_token.expires_at:
            return refresh_tokens(user_id, orm_token.refresh_token)

        return orm_token.access_token
    finally:
        db.close()

def refresh_tokens(user_id: str, refresh_token: str) -> str | None:
    """
    Use Strava’s refresh endpoint to get a new access token.
    """
    payload = {
        "client_id":     STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post("https://www.strava.com/api/v3/oauth/token", data=payload)

    if response.status_code != 200:
        print(f"❌ Failed to refresh token for {user_id}: {response.text}")
        return None

    new_tokens = response.json()
    # Save the newly returned tokens (this will update expires_at)
    save_tokens(user_id, new_tokens)
    return new_tokens.get("access_token")
