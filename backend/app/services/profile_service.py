"""Profile & Skill Scoring Service."""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import LearningProfile, ConceptSkill


def _mastery_from_score(score: int) -> str:
    """Classify mastery level from a 0–100 skill score.
    
    Thresholds (as per spec):
      score >= 80  → 'strong'
      score 50–79  → 'improving'
      score < 50   → 'beginner'
    """
    if score >= 80:
        return "strong"
    if score >= 50:
        return "improving"
    return "beginner"


def _canonical_language(language: str) -> str:
    lang = (language or "python").lower().strip()
    if lang in {"js", "node"}:
        return "javascript"
    if lang in {"c++", "cxx", "cc"}:
        return "cpp"
    if lang in {"rs"}:
        return "rust"
    return lang


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _normalize_concept_scores(concept_scores: Dict[str, Any] | None) -> Dict[str, int]:
    if not isinstance(concept_scores, dict):
        return {}

    normalized: Dict[str, int] = {}
    for concept, score in concept_scores.items():
        if not isinstance(concept, str):
            continue
        if isinstance(score, bool):
            continue
        if isinstance(score, (int, float)):
            normalized[concept.lower().strip()] = _clamp_score(score)
    return normalized


def update_learning_profile(db: Session, user_id: int, issues: List[Dict[str, Any]]):
    """Record mistakes in LearningProfile. Mastery will be set by update_skill_scores."""
    for issue in issues:
        concept = issue.get("concept", "General Python fundamentals")
        profile = (
            db.query(LearningProfile)
            .filter(LearningProfile.user_id == user_id, LearningProfile.concept == concept)
            .first()
        )

        if profile is None:
            profile = LearningProfile(
                user_id=user_id,
                concept=concept,
                mistake_count=1,
                mastery_level="beginner",
            )
            profile.last_seen = datetime.utcnow()
            db.add(profile)
        else:
            profile.mistake_count += 1
            profile.last_seen = datetime.utcnow()
            # mastery_level is updated in sync by update_skill_scores


def get_profile_summary(db: Session, user_id: int):
    """Return learning profiles, enriched with the numeric score from ConceptSkill."""
    profiles = db.query(LearningProfile).filter(LearningProfile.user_id == user_id).all()

    # Build a lookup: concept → score from ConceptSkill
    skill_rows = db.query(ConceptSkill).filter(ConceptSkill.user_id == user_id).all()
    skill_score_map: Dict[str, int] = {}
    for s in skill_rows:
        key = s.concept.lower()
        # Keep the highest score across languages for simplicity
        if key not in skill_score_map or s.score > skill_score_map[key]:
            skill_score_map[key] = s.score

    result = []
    for profile in profiles:
        score = skill_score_map.get(profile.concept.lower(), 0)
        result.append(
            {
                "concept": profile.concept,
                "mistake_count": profile.mistake_count,
                "mastery_level": profile.mastery_level,
                "score": score,
                "last_seen": profile.last_seen.isoformat(),
            }
        )
    return result


# ---------- Skill Graph Scoring ----------

def update_skill_scores(
    db: Session,
    user_id: int,
    concepts_detected: List[str],
    error_concepts: List[str],
    language: str = "python",
    understanding_score: int | None = None,
    concept_scores: Dict[str, Any] | None = None,
):
    """Update concept skill scores. Concepts without errors get correct_usage++.
    Also syncs mastery_level on LearningProfile rows using the score-based classifier.
    """
    error_set = set(c.lower() for c in error_concepts)
    canonical_language = _canonical_language(language)
    per_concept_ai_scores = _normalize_concept_scores(concept_scores)
    base_understanding = _clamp_score(understanding_score if understanding_score is not None else 60)

    # Bayesian smoothing avoids first-attempt binary scores (0 or 100).
    prior_strength = 2
    prior_mean = base_understanding / 100.0

    for concept in concepts_detected:
        skill = (
            db.query(ConceptSkill)
            .filter(
                ConceptSkill.user_id == user_id,
                ConceptSkill.concept == concept,
                ConceptSkill.language == canonical_language,
            )
            .first()
        )
        if skill is None:
            skill = ConceptSkill(
                user_id=user_id,
                concept=concept,
                language=canonical_language,
                correct_usage=0,
                total_usage=0,
                score=0,
            )
            db.add(skill)

        skill.total_usage += 1
        if concept.lower() not in error_set:
            skill.correct_usage += 1

        smoothed_ratio = (
            skill.correct_usage + (prior_strength * prior_mean)
        ) / (max(skill.total_usage, 1) + prior_strength)
        usage_score = _clamp_score(smoothed_ratio * 100)

        ai_concept_score = per_concept_ai_scores.get(concept.lower().strip())
        if ai_concept_score is not None:
            # Blend concept usage with model understanding for concept-level nuance.
            skill.score = _clamp_score((0.7 * usage_score) + (0.3 * ai_concept_score))
        else:
            skill.score = usage_score

        skill.last_updated = datetime.utcnow()

        # Sync mastery level onto LearningProfile row (if it exists)
        profile = (
            db.query(LearningProfile)
            .filter(LearningProfile.user_id == user_id, LearningProfile.concept == concept)
            .first()
        )
        if profile is not None:
            profile.mastery_level = _mastery_from_score(skill.score)


def get_skill_scores(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """Return all skill scores for a user, including mastery level."""
    skills = db.query(ConceptSkill).filter(ConceptSkill.user_id == user_id).all()
    return [
        {
            "concept": s.concept,
            "language": s.language,
            "correct_usage": s.correct_usage,
            "total_usage": s.total_usage,
            "score": s.score,
            "mastery_level": _mastery_from_score(s.score),
        }
        for s in skills
    ]
