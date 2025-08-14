# backend/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.services.passwords import hash_password, verify_password
import secrets
from backend.deps.auth import get_db, get_current_user
from backend.db.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])

class UpdateMe(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None
    class Config: from_attributes = True

# def get_db():
#     db = SessionLocal()
#     try: yield db
#     finally: db.close()

def require_csrf(request: Request):
    sess = request.session.get("csrf")
    hdr  = request.headers.get("X-CSRF-Token")
    if not sess or not hdr or hdr != sess:
        raise HTTPException(status_code=403, detail="CSRF check failed")

@router.get("/csrf")
def get_csrf(request: Request):
    token = secrets.token_urlsafe(32)
    request.session["csrf"] = token
    return {"csrf": token}

@router.post("/register", response_model=UserOut)
def register(payload: RegisterIn, request: Request, db: Session = Depends(get_db)):
    require_csrf(request)
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=hash_password(payload.password), name=payload.name)
    db.add(user); db.commit(); db.refresh(user)
    request.session["user_id"] = user.id
    return user

@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    require_csrf(request)
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    request.session["user_id"] = user.id
    return user

@router.post("/logout")
def logout(request: Request):
    require_csrf(request)
    request.session.clear()
    return {"message": "ok"}

@router.get("/me", response_model=UserOut | None)
def me(request: Request, db: Session = Depends(get_db)):
    uid = request.session.get("user_id")
    if not uid: return None
    return db.get(User, uid)

@router.put("/me")
def update_me(
    payload: UpdateMe,
    request: Request,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    # CSRF
    sess = request.session.get("csrf")
    hdr = request.headers.get("X-CSRF-Token")
    if not sess or not hdr or hdr != sess:
        raise HTTPException(status_code=403, detail="CSRF check failed")

    # Reload user in this session
    db_user = db.get(User, me.id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Email uniqueness (exclude me)
    if payload.email and payload.email != db_user.email:
        exists = (
            db.query(User)
              .filter(User.email == payload.email, User.id != db_user.id)
              .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Email already in use")
        db_user.email = payload.email

    if payload.name is not None:
        db_user.name = payload.name.strip()

    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "email": db_user.email, "name": db_user.name}
