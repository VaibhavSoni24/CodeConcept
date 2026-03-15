from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserSubscription
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])


PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "credits_per_month": 150,
        "included_analyses": 30,
        "features": ["Basic dashboard", "Core analysis", "Community support"],
    },
    "student-lite": {
        "name": "Student Lite",
        "price_monthly": 9,
        "credits_per_month": 750,
        "included_analyses": 150,
        "features": ["Full dashboard", "Knowledge hub", "Priority email support"],
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 19,
        "credits_per_month": 2500,
        "included_analyses": 500,
        "features": ["Advanced analysis", "Faster queue", "Export reports"],
    },
    "team": {
        "name": "Team",
        "price_monthly": 79,
        "credits_per_month": 10000,
        "included_analyses": 2000,
        "features": ["5 seats included", "Cohort analytics", "Instructor insights"],
    },
}

CREDIT_PACKS: Dict[str, Dict[str, Any]] = {
    "pack-100": {"name": "100 Analyses", "price": 5, "credits": 500},
    "pack-500": {"name": "500 Analyses", "price": 20, "credits": 2500},
    "pack-1000": {"name": "1000 Analyses", "price": 35, "credits": 5000},
}


def _get_or_create_subscription(db: Session, user_id: int) -> UserSubscription:
    sub = db.query(UserSubscription).filter(UserSubscription.user_id == user_id).first()
    if sub:
        return sub

    base = PLANS["free"]
    sub = UserSubscription(
        user_id=user_id,
        plan_name="free",
        price_monthly=base["price_monthly"],
        credits_per_month=base["credits_per_month"],
        status="active",
        renewed_at=datetime.utcnow(),
    )
    db.add(sub)
    db.flush()
    return sub


@router.get("/plans")
def get_plans(_current_user: User = Depends(get_current_user)):
    return {"plans": PLANS, "credit_packs": CREDIT_PACKS}


@router.get("/users/{user_id}/subscription")
def get_subscription(user_id: int, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    if _current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sub = _get_or_create_subscription(db, user_id)
    db.commit()

    return {
        "plan_key": sub.plan_name,
        "plan": PLANS.get(sub.plan_name, PLANS["free"]),
        "status": sub.status,
        "renewed_at": sub.renewed_at.isoformat() if sub.renewed_at else None,
    }


@router.post("/users/{user_id}/subscribe/{plan_key}")
def subscribe_plan(user_id: int, plan_key: str, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    if _current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if plan_key not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = PLANS[plan_key]
    sub = _get_or_create_subscription(db, user_id)
    sub.plan_name = plan_key
    sub.price_monthly = plan["price_monthly"]
    sub.credits_per_month = plan["credits_per_month"]
    sub.status = "active"
    sub.renewed_at = datetime.utcnow()

    # Dummy payment success: instantly allocate monthly credits.
    user.credits += plan["credits_per_month"]

    db.commit()

    return {
        "message": "Subscription updated (dummy payment mode)",
        "plan_key": sub.plan_name,
        "plan": plan,
        "status": sub.status,
        "credits": user.credits,
    }


@router.post("/users/{user_id}/topup/{pack_key}")
def topup_credits(user_id: int, pack_key: str, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    if _current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if pack_key not in CREDIT_PACKS:
        raise HTTPException(status_code=400, detail="Invalid credit pack")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    pack = CREDIT_PACKS[pack_key]
    user.credits += pack["credits"]
    db.commit()

    return {
        "message": "Credit top-up successful (dummy payment mode)",
        "pack": pack,
        "credits": user.credits,
    }


@router.get("/metrics")
def get_billing_metrics(db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    rows = db.query(UserSubscription).all()

    plan_counts: Dict[str, int] = {k: 0 for k in PLANS.keys()}
    for r in rows:
        key = r.plan_name if r.plan_name in plan_counts else "free"
        plan_counts[key] += 1

    mrr = sum(plan_counts[k] * PLANS[k]["price_monthly"] for k in plan_counts)

    # Simple simulated infra model.
    base_infra = 250
    per_paid_user = 2.0
    paid_users = sum(v for k, v in plan_counts.items() if k != "free")
    estimated_cost = round(base_infra + paid_users * per_paid_user, 2)

    return {
        "plan_counts": plan_counts,
        "mrr": mrr,
        "estimated_monthly_cost": estimated_cost,
        "estimated_gross_margin_percent": (round(((mrr - estimated_cost) / mrr) * 100, 2) if mrr > 0 else 0),
    }
