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


def update_learning_profile(db: Session, user_id: int, issues: List[Dict[str, Any]], concepts_detected: List[str] = None):
    if concepts_detected is None:
        concepts_detected = []
        
    error_concepts = set()
    for issue in issues:
        concept = issue.get("concept", "General Python fundamentals")
        error_concepts.add(concept)
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

    # If there are any actual issues in the code, do not grant positive progress on any concept detected.
    if issues:
        error_concepts.update(concepts_detected)

    for concept in concepts_detected:
        if concept not in error_concepts:
            profile = (
                db.query(LearningProfile)
                .filter(LearningProfile.user_id == user_id, LearningProfile.concept == concept)
                .first()
            )
            if profile is None:
                profile = LearningProfile(user_id=user_id, concept=concept, mistake_count=0)
                profile.mastery_level = _mastery_from_mistakes(0)
                profile.last_seen = datetime.utcnow()
                db.add(profile)
            else:
                profile.last_seen = datetime.utcnow()
                if profile.mistake_count > 0:
                    profile.mistake_count -= 1
                    profile.mastery_level = _mastery_from_mistakes(profile.mistake_count)


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
    all_concepts = set(concepts_detected) | error_set  # Union of all observed concepts

    for concept in all_concepts:
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

        # Calculate a progressive score
        # Starts easily but requires more effort to reach 100
        # e.g., 1 correct = 20, 3 correct = 50, 10 correct = 85, 20 correct = 95
        import math
        base_score = 0
        if skill.correct_usage > 0:
            # logarithmic curve scaling up to 100
            progress = min(skill.correct_usage / 20.0, 1.0) # maxes out around 20 correct uses
            base_score = int(100 * (1.0 - math.exp(-3 * progress)))

        # Penalize slightly for overall error rate
        accuracy_penalty = 0
        if skill.total_usage > 0:
            error_rate = 1.0 - (skill.correct_usage / skill.total_usage)
            accuracy_penalty = int(error_rate * 20)  # Max 20 point penalty for errors

        skill.score = max(0, min(100, base_score - accuracy_penalty))
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
