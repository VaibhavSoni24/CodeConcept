from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import User, ConceptSkill, Submission
from ..services.auth_service import get_current_user
from ..services.youtube_service import get_learning_videos

router = APIRouter(tags=["knowledge"])


def _canonical_language(language: str) -> str:
    lang = (language or "python").lower().strip()
    if lang in {"js", "node"}:
        return "javascript"
    if lang in {"c++", "cxx", "cc"}:
        return "cpp"
    if lang in {"rs"}:
        return "rust"
    return lang


def _level_from_score(score: int) -> str:
    if score >= 70:
        return "Strong"
    if score >= 30:
        return "Moderate"
    return "Needs Practice"


def _build_knowledge_payload(skills: List[ConceptSkill], submissions: List[Any]) -> Dict[str, Any]:
    languages_dict: Dict[str, Any] = {}
    concept_totals: Dict[str, Dict[str, int]] = {}

    for skill in skills:
        score = int((skill.correct_usage / max(skill.total_usage, 1)) * 100)
        lang_key = _canonical_language(skill.language)

        if lang_key not in languages_dict:
            languages_dict[lang_key] = {
                "concept_scores": [],
                "total_correct": 0,
                "total_usage": 0,
            }

        languages_dict[lang_key]["concept_scores"].append(
            {
                "concept": skill.concept.replace("_", " ").title(),
                "score": score,
            }
        )
        languages_dict[lang_key]["total_correct"] += skill.correct_usage
        languages_dict[lang_key]["total_usage"] += skill.total_usage

        c_mapped = skill.concept.replace("_", " ").title()
        if c_mapped not in concept_totals:
            concept_totals[c_mapped] = {"correct": 0, "total": 0}

        concept_totals[c_mapped]["correct"] += skill.correct_usage
        concept_totals[c_mapped]["total"] += skill.total_usage

    concepts_learned = []
    for c_name, counts in concept_totals.items():
        avg_score = int((counts["correct"] / max(counts["total"], 1)) * 100)
        concepts_learned.append(
            {
                "concept": c_name,
                "score": avg_score,
                "level": _level_from_score(avg_score),
            }
        )

    sorted_concepts = sorted(concepts_learned, key=lambda x: x["score"])

    language_summary = []
    for lang, data in languages_dict.items():
        avg_lang_score = int((data["total_correct"] / max(data["total_usage"], 1)) * 100)
        language_summary.append(
            {
                "language": lang,
                "avg_score": avg_lang_score,
                "concept_count": len(data["concept_scores"]),
                "attempts": data["total_usage"],
            }
        )
    language_summary.sort(key=lambda x: x["avg_score"], reverse=True)

    mastery_distribution = {"Strong": 0, "Moderate": 0, "Needs Practice": 0}
    for item in sorted_concepts:
        mastery_distribution[item["level"]] += 1

    submission_counts = {_canonical_language(lang): count for lang, count in submissions}
    for lang in languages_dict.keys():
        submission_counts.setdefault(lang, 0)

    language_activity = [
        {"language": lang, "submissions": count}
        for lang, count in sorted(submission_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "languages": languages_dict,
        "concepts_learned": sorted_concepts,
        "language_summary": language_summary,
        "language_activity": language_activity,
        "mastery_distribution": [
            {"name": "Strong", "value": mastery_distribution["Strong"]},
            {"name": "Moderate", "value": mastery_distribution["Moderate"]},
            {"name": "Needs Practice", "value": mastery_distribution["Needs Practice"]},
        ],
    }

@router.get("/users/{user_id}/knowledge-recommendations")
def get_knowledge_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    skills = db.query(ConceptSkill).filter(ConceptSkill.user_id == user_id).all()
    submissions = (
        db.query(Submission.language, func.count(Submission.id))
        .filter(Submission.user_id == user_id)
        .group_by(Submission.language)
        .all()
    )

    payload = _build_knowledge_payload(skills, submissions)

    CORE_CONCEPTS = [
        "Variables", "Loops", "Conditionals", "Functions", 
        "Data Structures", "Recursion", "Error Handling", 
        "Object Oriented Programming"
    ]

    visited_concepts = [c["concept"] for c in payload["concepts_learned"]]
    unvisited = [c for c in CORE_CONCEPTS if c not in visited_concepts]

    weak_concepts = [str(c["concept"]) for c in payload["concepts_learned"] if int(str(c["score"])) < 70]

    target_concepts: List[str] = []
    for c in (unvisited + weak_concepts):
        if c not in target_concepts:
            target_concepts.append(c)

    if not target_concepts:
        target_concepts = ["Data Structures and Algorithms"]

    videos = get_learning_videos(target_concepts, max_total=5)

    return {**payload, "youtube_recommendations": videos}


@router.get("/knowledge/global-summary")
def get_global_knowledge_summary(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    skills = db.query(ConceptSkill).all()
    submissions = (
        db.query(Submission.language, func.count(Submission.id))
        .group_by(Submission.language)
        .all()
    )

    payload = _build_knowledge_payload(skills, submissions)
    payload["youtube_recommendations"] = []
    payload["global_users"] = db.query(func.count(User.id)).scalar() or 0
    payload["global_skill_rows"] = len(skills)
    return payload
