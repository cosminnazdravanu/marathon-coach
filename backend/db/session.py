# backend/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base
import os

SQLALCHEMY_DATABASE_URL = "sqlite:///backend/db/RunningCoach.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ❌ REMOVE this in an Alembic-managed project:
# Base.metadata.create_all(bind=engine)

# Optional dev-only escape hatch (off by default):
if os.getenv("DB_CREATE_ALL") == "1":
    Base.metadata.create_all(bind=engine)
