from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import LearningProfile


def _mastery_from_mistakes(mistake_count: int) -> str:
    if mistake_count >= 6:
        return "struggling"
    if mistake_count >= 3:
        return "beginner"
    return "improving"


def update_learning_profile(db: Session, user_id: int, issues: List[Dict[str, Any]]):
    for issue in issues:
        concept = issue.get("concept", "General Python fundamentals")
        profile = (
            db.query(LearningProfile)
            .filter(LearningProfile.user_id == user_id, LearningProfile.concept == concept)
            .first()
        )

        if profile is None:
            profile = LearningProfile(user_id=user_id, concept=concept, mistake_count=1)
            profile.mastery_level = _mastery_from_mistakes(profile.mistake_count)
            profile.last_seen = datetime.utcnow()
            db.add(profile)
        else:
            profile.mistake_count += 1
            profile.mastery_level = _mastery_from_mistakes(profile.mistake_count)
            profile.last_seen = datetime.utcnow()


def get_profile_summary(db: Session, user_id: int):
    profiles = db.query(LearningProfile).filter(LearningProfile.user_id == user_id).all()
    return [
        {
            "concept": profile.concept,
            "mistake_count": profile.mistake_count,
            "mastery_level": profile.mastery_level,
            "last_seen": profile.last_seen.isoformat(),
        }
        for profile in profiles
    ]
