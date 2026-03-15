from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas.payloads import CreateUserRequest, UserOut
from ..services.auth_service import get_current_user
from ..services.profile_service import get_profile_summary, get_skill_scores

router = APIRouter(tags=["profiles"])


@router.post("/users", response_model=UserOut)
def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)):
    user = User(name=payload.name, email=payload.email, level=payload.level)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/profiles/{user_id}")
def profile(user_id: int, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    summary = get_profile_summary(db, user_id)
    skill_scores = get_skill_scores(db, user_id)
    return {"user_id": user_id, "profiles": summary, "skill_scores": skill_scores}


@router.get("/users/{user_id}/credits")
def get_credits(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"credits": user.credits}
