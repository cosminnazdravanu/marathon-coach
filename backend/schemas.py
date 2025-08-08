# backend/schemas.py

from pydantic import BaseModel
from typing import Optional
from datetime import date

class TrainingPlan(BaseModel):
    id: Optional[int] = None
    date: date
    type: Optional[str] = None
    description: Optional[str] = None
    warmup_target: Optional[str] = None
    main_target: Optional[str] = None
    cooldown_target: Optional[str] = None
    terrain: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True      # replaces orm_mode in Pydantic v2
        json_schema_extra = {
            "example": {
                "id": 1,
                "date": "2025-08-10", 
                "type": "Long Run",
                "description": "Build endurance with a steady 20 km run",
                "warmup_target": "3 km easy",
                "main_target": "14 km steady",
                "cooldown_target": "3 km easy",
                "terrain": "flat",
                "notes": "Keep HR in Z2"
            }
        }
