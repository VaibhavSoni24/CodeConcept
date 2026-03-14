from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Submission, User
from ..services.auth_service import get_current_user

router = APIRouter(tags=["activity"])

@router.get("/users/{user_id}/submissions")
def get_user_submissions(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    submissions = db.query(Submission).filter(Submission.user_id == user_id).order_by(Submission.timestamp.desc()).all()
    return [{
        "id": s.id, 
        "code": s.code, 
        "language": s.language, 
        "result": s.result, 
        "timestamp": s.timestamp.isoformat(), 
        "analysis_result": s.analysis_result if s.analysis_result else {}
    } for s in submissions]
