import time
import os
import base64
import hashlib
import httpx
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models import StravaToken as ORMStravaToken
from backend.config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET
from cryptography.fernet import Fernet, InvalidToken

def _build_key() -> bytes:
    """
    Accept a proper Fernet key (urlsafe base64) if provided in TOKENS_KEY.
    Otherwise derive a Fernet key from SECRET_KEY (or a dev default) via SHA-256.
    """
    raw = os.getenv("TOKENS_KEY") or os.getenv("SECRET_KEY") or "dev-unsafe"
    try:
        # If this succeeds, it's a Fernet key already
        base64.urlsafe_b64decode(raw.encode())
        return raw.encode()
    except Exception:
        return base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())

_F = Fernet(_build_key())

def _enc(s: str | None) -> str | None:
    if not s:
        return s
    return _F.encrypt(s.encode()).decode()

def _dec(s: str | None) -> str | None:
    if not s:
        return s
    # Backward compatibility: if old plaintext is stored, just return it.
    try:
        return _F.decrypt(s.encode()).decode()
    except InvalidToken:
        return s

def save_tokens(user_id: str, tokens: dict) -> None:
    """
    Insert or update Strava tokens for a user, storing them encrypted at rest.
    """
    expires_at    = tokens.get("expires_at", int(time.time()) + 2100)
    access_token  = _enc(tokens.get("access_token"))
    refresh_token = _enc(tokens.get("refresh_token"))

    db: Session = SessionLocal()
    try:
        orm_token = db.get(ORMStravaToken, user_id)
        if not orm_token:
            orm_token = ORMStravaToken(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            db.add(orm_token)
        else:
            # Always take newest values
            if access_token:
                orm_token.access_token = access_token
            if refresh_token:
                orm_token.refresh_token = refresh_token
            orm_token.expires_at = expires_at
        db.commit()
    finally:
        db.close()

def get_access_token(user_id: str) -> str | None:
    """
    Return a valid access token (decrypting as needed). Refresh if expired.
    """
    db: Session = SessionLocal()
    try:
        orm_token = db.get(ORMStravaToken, user_id)
        if not orm_token:
            print(f"[TOKENS] no row for user_id={user_id!r}")
            return None

        if time.time() > orm_token.expires_at:
            # Decrypt refresh token before use
            rtok = _dec(orm_token.refresh_token)
            return refresh_tokens(user_id, rtok)
        
        return _dec(orm_token.access_token)
    finally:
        db.close()

def refresh_tokens(user_id: str, refresh_token: str | None) -> str | None:
    if not refresh_token:
        print(f"❌ No refresh token available for {user_id}")
        return None

    payload = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post("https://www.strava.com/api/v3/oauth/token", data=payload)
            resp.raise_for_status()
        new_tokens = resp.json()
        save_tokens(user_id, new_tokens)
        return new_tokens.get("access_token")
    except httpx.HTTPError as e:
        print(f"❌ Failed to refresh token for {user_id}: {e}")
        return None

def delete_tokens(user_id: str) -> None:
    db: Session = SessionLocal()
    try:
        orm = db.get(ORMStravaToken, user_id)
        if orm:
            db.delete(orm)
            db.commit()
    finally:
        db.close()