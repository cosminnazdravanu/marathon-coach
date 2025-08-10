# backend/db/models.py
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, UniqueConstraint, func, Index
from sqlalchemy.orm import relationship
from .base import Base

class TrainingPlan(Base):
    __tablename__ = "training_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # NEW:
    user_id = Column(Integer, nullable=True, index=True)  # keep nullable for SQLite; enforce in app
    date = Column(String, nullable=False)
    type = Column(String, nullable=True)
    description = Column(String, nullable=True)
    warmup_target = Column(String, nullable=True)
    main_target = Column(String, nullable=True)
    cooldown_target = Column(String, nullable=True)
    terrain = Column(String, nullable=True)
    notes = Column(String, nullable=True)

class StravaToken(Base):
    __tablename__ = "strava_tokens"
    user_id       = Column(String,  primary_key=True)
    access_token  = Column(String,  nullable=False)
    refresh_token = Column(String,  nullable=False)
    expires_at    = Column(Integer, nullable=False)

class User(Base):
    __tablename__ = "users"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    email        = Column(String, unique=True, index=True, nullable=False)
    password_hash= Column(String, nullable=False)
    name         = Column(String, nullable=True)
    avatar_url   = Column(String, nullable=True)
    created_at   = Column(DateTime, server_default=func.now())
    updated_at   = Column(DateTime, onupdate=func.now())

    identities   = relationship("AuthIdentity", back_populates="user", cascade="all, delete-orphan")

class AuthIdentity(Base):
    __tablename__ = "auth_identities"
    id               = Column(Integer, primary_key=True, autoincrement=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider         = Column(String, nullable=False)          # "google" | "apple" | "facebook" | "strava"
    provider_user_id = Column(String, nullable=False)          # e.g. Google sub / Strava athlete.id
    email_from_provider = Column(String, nullable=True)
    access_token_enc = Column(Text, nullable=True)             # encrypted at rest (reuse your Fernet helper)
    refresh_token_enc= Column(Text, nullable=True)
    expires_at       = Column(Integer, nullable=True)

    user = relationship("User", back_populates="identities")
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),)