from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, ConceptSkill
from ..services.auth_service import get_current_user
from ..services.youtube_service import get_learning_videos

router = APIRouter(tags=["knowledge"])

@router.get("/users/{user_id}/knowledge-recommendations")
def get_knowledge_recommendations(user_id: int, db: Session = Depends(get_db)):
    # 1. Fetch total skill scores for the user across all languages
    skills = db.query(ConceptSkill).filter(ConceptSkill.user_id == user_id).all()
    
    # Optional logic: If empty, we can handle it frontend side.
    if not skills:
        return {
            "languages": {},
            "concepts_learned": [],
            "youtube_recommendations": []
        }
    
    # 2. Re-calculate actual 0-100 percentage if not natively correct & Group by language
    languages_dict: Dict[str, Any] = {}
    
    # 3. Aggregate Concepts Learned table 
    # Since a concept might appear in multiple languages, we average its mastery overall
    concept_totals: Dict[str, Dict[str, int]] = {}
    
    for skill in skills:
        score = int((skill.correct_usage / max(skill.total_usage, 1)) * 100)
        
        # Hydrate lang radar chart mapping
        if skill.language not in languages_dict:
            languages_dict[skill.language] = {"concept_scores": []}
            
        languages_dict[skill.language]["concept_scores"].append({
            "concept": skill.concept.replace("_", " ").title(),
            "score": score
        })
        
        # Tally holistic concept score
        c_mapped = skill.concept.replace("_", " ").title()
        if c_mapped not in concept_totals:
             concept_totals[c_mapped] = {"correct": 0, "total": 0}
        
        concept_totals[c_mapped]["correct"] += skill.correct_usage
        concept_totals[c_mapped]["total"] += skill.total_usage
        
    # Build 'Concepts Learned' ranking array
    concepts_learned = []
    for c_name, counts in concept_totals.items():
         avg_score = int((counts["correct"] / max(counts["total"], 1)) * 100)
         
         # Level Classifier
         if avg_score >= 70:
             level = "Strong"
         elif avg_score >= 30:
             level = "Moderate"
         else:
             level = "Needs Practice"
             
         concepts_learned.append({
             "concept": c_name,
             "score": avg_score,
             "level": level
         })
         
    # 4. Filter lowest-scoring concepts for Youtube API
    # Sort by holistic score ascending
    sorted_concepts = sorted(concepts_learned, key=lambda x: x["score"])
    
    target_concepts = [c["concept"] for c in sorted_concepts[:2]] # Take 2 weakest 
    
    videos = get_learning_videos(target_concepts)
    
    return {
        "languages": languages_dict,
        "concepts_learned": sorted_concepts,
        "youtube_recommendations": videos
    }
