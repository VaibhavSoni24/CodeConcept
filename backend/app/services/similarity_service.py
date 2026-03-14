from sqlalchemy.orm import Session
from ..models import Submission
from typing import Optional
import difflib

def check_code_similarity(db: Session, current_user_id: int, code: str, language: str) -> Optional[float]:
    """
    Finds the highest similarity score between the provided code and previous
    submissions of the same language by the same user.
    Uses Python's built-in difflib for a basic implementation.
    """
    recent_submissions = db.query(Submission)\
        .filter(Submission.user_id == current_user_id)\
        .filter(Submission.language == language)\
        .order_by(Submission.timestamp.desc())\
        .limit(10)\
        .all()
        
    if not recent_submissions:
        return 0.0
        
    max_ratio = 0.0
    for sub in recent_submissions:
        ratio = difflib.SequenceMatcher(None, code, sub.code).ratio()
        if ratio > max_ratio:
            max_ratio = ratio
            
    return round(max_ratio, 2)
