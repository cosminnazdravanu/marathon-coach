# backend/deps/auth.py
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models import User

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    uid = request.session.get("user_id")
    if not uid: raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.get(User, uid)
    if not user: raise HTTPException(status_code=401, detail="Not authenticated")
    return user
