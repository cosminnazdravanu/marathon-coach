# backend/db/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .base import Base
from .models import TrainingPlan, StravaToken

DB_PATH = os.path.join(os.path.dirname(__file__), "RunningCoach.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_models():
    # only for one-off bootstrap; Alembic will thereafter manage schema
    Base.metadata.create_all(bind=engine)
