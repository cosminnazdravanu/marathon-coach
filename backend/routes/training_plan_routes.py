# backend/routes/training_plan_routes.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.db.models import TrainingPlan as ORMTrainingPlan
from backend.schemas import TrainingPlan
from backend.deps.auth import get_current_user

router = APIRouter(tags=["Training Plans"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def require_csrf(request: Request):
    sess = request.session.get("csrf")
    hdr = request.headers.get("X-CSRF-Token")
    if not sess or not hdr or hdr != sess:
        raise HTTPException(status_code=403, detail="CSRF check failed")

@router.get("/plans", response_model=List[TrainingPlan])
def get_all_plans(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return (
        db.query(ORMTrainingPlan)
        .filter(ORMTrainingPlan.user_id == current_user.id)
        .order_by(ORMTrainingPlan.date.asc(), ORMTrainingPlan.id.asc())
        .all()
    )

@router.post("/plans", status_code=201)
def add_plan(
    plan: TrainingPlan,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    require_csrf(request)
    data = plan.model_dump(exclude={"id"})
    data["type"] = "planned"
    orm_plan = ORMTrainingPlan(
        **data,
        user_id=current_user.id,   # 👈 set owner
    )
    db.add(orm_plan)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(orm_plan)
    return {"message": "Plan added", "id": orm_plan.id}

def _get_owned_plan(db: Session, plan_id: int, user_id: int) -> ORMTrainingPlan | None:
    return (
        db.query(ORMTrainingPlan)
        .filter(ORMTrainingPlan.id == plan_id, ORMTrainingPlan.user_id == user_id)
        .order_by(ORMTrainingPlan.date.asc(), ORMTrainingPlan.id.asc())
        .first()
    )

@router.put("/plans/{plan_id}")
def update_plan(
    plan_id: int,
    plan: TrainingPlan,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    require_csrf(request)
    orm_plan = _get_owned_plan(db, plan_id, current_user.id)
    if not orm_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, value in plan.model_dump(exclude={"id"}).items():
        if field == "type":
            value = "planned"
        setattr(orm_plan, field, value)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Plan updated"}

@router.patch("/plans/{plan_id}")
def patch_plan(
    plan_id: int,
    plan: TrainingPlan,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    require_csrf(request)
    orm_plan = _get_owned_plan(db, plan_id, current_user.id)
    if not orm_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    orm_plan.date = plan.date
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Plan date updated"}

@router.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    require_csrf(request)
    orm_plan = _get_owned_plan(db, plan_id, current_user.id)
    if not orm_plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(orm_plan)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Plan deleted"}
