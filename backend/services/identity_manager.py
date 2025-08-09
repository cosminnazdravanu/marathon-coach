# backend/services/identity_manager.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal

def link_strava_identity(local_user_id: int, tokens: dict) -> None:
    """
    Persist the link between this local user and the Strava account.
    Enforces uniqueness: a Strava account can't be linked to two local users.
    """
    provider = "strava"
    athlete = tokens.get("athlete") or {}
    provider_user_id = str(athlete.get("id"))
    email_from_provider = athlete.get("email")  # often absent; fine if None

    if not provider_user_id:
        # First-time code exchange should include athlete; if you're doing this after a refresh
        # you'll need to call /athlete to look it up.
        raise ValueError("Missing athlete.id in tokens")

    db: Session = SessionLocal()
    try:
        # Is this Strava account already linked to someone else?
        row = db.execute(
            text("""
                SELECT user_id FROM auth_identities
                WHERE provider='strava' AND provider_user_id=:pid
            """),
            {"pid": provider_user_id},
        ).fetchone()

        if row and int(row[0]) != int(local_user_id):
            raise ValueError("This Strava account is already linked to another user.")

        # Upsert link
        db.execute(
            text("""
                INSERT INTO auth_identities (user_id, provider, provider_user_id, email_from_provider)
                VALUES (:uid, 'strava', :pid, :email)
                ON CONFLICT(provider, provider_user_id) DO UPDATE SET
                    user_id = excluded.user_id,
                    email_from_provider = excluded.email_from_provider
            """),
            {"uid": local_user_id, "pid": provider_user_id, "email": email_from_provider},
        )
        db.commit()
    finally:
        db.close()

def unlink_strava_identity(local_user_id: int) -> None:
    db: Session = SessionLocal()
    try:
        db.execute(
            text("DELETE FROM auth_identities WHERE provider='strava' AND user_id=:uid"),
            {"uid": local_user_id},
        )
        db.commit()
    finally:
        db.close()
