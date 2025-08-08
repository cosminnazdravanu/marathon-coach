# backend/routes/training_plan_routes.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.schemas import TrainingPlan
from backend.db.models import TrainingPlan as ORMTrainingPlan

router = APIRouter(tags=["Training Plans"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# # 2) Pydantic schema can stay mostly the same (no id on input)
# class TrainingPlan(BaseModel):
#     id: Optional[int] = None
#     date: str
#     type: Optional[str] = None
#     description: Optional[str] = None
#     warmup_target: Optional[str] = None
#     main_target: Optional[str] = None
#     cooldown_target: Optional[str] = None
#     terrain: Optional[str] = None
#     notes: Optional[str] = None

#     class Config:
#         from_attributes = True
#         schema_extra = {
#             "example": {
#                 "id": 1,
#                 "date": "2025-08-10",
#                 "type": "Long Run",
#                 "description": "Build endurance with a steady 20 km run",
#                 "warmup_target": "3 km easy",
#                 "main_target": "14 km steady",
#                 "cooldown_target": "3 km easy",
#                 "terrain": "flat",
#                 "notes": "Keep HR in Z2"
#             }
#         }

# 3) Dependency to get a DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @router.get("/plans")
# def get_all_plans(db: Session = Depends(get_db)):
#     # Fetch all ORM objects
#     plans = db.query(ORMTrainingPlan).all()

#     # Convert to dicts and group by date
#     grouped: dict[str, List[dict]] = {}
#     for p in plans:
#         item = {
#             "id": p.id,
#             "date": p.date,
#             "type": p.type,
#             "description": p.description,
#             "warmup_target": p.warmup_target,
#             "main_target": p.main_target,
#             "cooldown_target": p.cooldown_target,
#             "terrain": p.terrain,
#             "notes": p.notes,
#         }
#         grouped.setdefault(p.date, []).append(item)

#     return grouped

@router.get("/plans", response_model=List[TrainingPlan])
def get_all_plans(db: Session = Depends(get_db)):
    return db.query(ORMTrainingPlan).all()

@router.post("/plans", status_code=201)
def add_plan(plan: TrainingPlan, db: Session = Depends(get_db)):
    orm_plan = ORMTrainingPlan(**plan.dict(exclude={"id"}))
    db.add(orm_plan)
    db.commit()
    db.refresh(orm_plan)
    return {"message": "Plan added", "id": orm_plan.id}

@router.put("/plans/{plan_id}")
def update_plan(plan_id: int, plan: TrainingPlan, db: Session = Depends(get_db)):
    orm_plan = db.get(ORMTrainingPlan, plan_id)
    if not orm_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, value in plan.dict(exclude={"id"}).items():
        setattr(orm_plan, field, value)
    db.commit()
    return {"message": "Plan updated"}

@router.patch("/plans/{plan_id}")
def patch_plan(plan_id: int, plan: TrainingPlan, db: Session = Depends(get_db)):
    orm_plan = db.get(ORMTrainingPlan, plan_id)
    if not orm_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    # Only update date
    orm_plan.date = plan.date
    db.commit()
    return {"message": "Plan date updated"}

@router.delete("/plans/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    orm_plan = db.get(ORMTrainingPlan, plan_id)
    if not orm_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(orm_plan)
    db.commit()
    return {"message": "Plan deleted"}
