"""Profile & Skill Scoring Service."""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import LearningProfile, ConceptSkill


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


# ---------- Skill Graph Scoring ----------

def update_skill_scores(
    db: Session,
    user_id: int,
    concepts_detected: List[str],
    error_concepts: List[str],
):
    """Update concept skill scores. Concepts without errors get correct_usage++."""
    error_set = set(error_concepts)

    for concept in concepts_detected:
        skill = (
            db.query(ConceptSkill)
            .filter(ConceptSkill.user_id == user_id, ConceptSkill.concept == concept)
            .first()
        )
        if skill is None:
            skill = ConceptSkill(
                user_id=user_id,
                concept=concept,
                correct_usage=0,
                total_usage=0,
                score=0,
            )
            db.add(skill)

        skill.total_usage += 1
        if concept not in error_set:
            skill.correct_usage += 1

        skill.score = int((skill.correct_usage / max(skill.total_usage, 1)) * 100)
        skill.last_updated = datetime.utcnow()


def get_skill_scores(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Return all skill scores for a user."""
    skills = db.query(ConceptSkill).filter(ConceptSkill.user_id == user_id).all()
    return [
        {
            "concept": s.concept,
            "correct_usage": s.correct_usage,
            "total_usage": s.total_usage,
            "score": s.score,
        }
        for s in skills
    ]
