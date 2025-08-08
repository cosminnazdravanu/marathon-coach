# backend/db/models.py
from sqlalchemy import Column, Integer, String, Text, Date
from .base import Base

class TrainingPlan(Base):
    __tablename__ = "training_plan"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    date            = Column(String,  nullable=False)
    type            = Column(String,  nullable=True)
    description     = Column(Text,    nullable=True)
    warmup_target   = Column(String,  nullable=True)
    main_target     = Column(String,  nullable=True)
    cooldown_target = Column(String,  nullable=True)
    terrain         = Column(String,  nullable=True)
    notes           = Column(Text,    nullable=True)

class StravaToken(Base):
    __tablename__ = "strava_tokens"
    user_id       = Column(String,  primary_key=True)
    access_token  = Column(String,  nullable=False)
    refresh_token = Column(String,  nullable=False)
    expires_at    = Column(Integer, nullable=False)
