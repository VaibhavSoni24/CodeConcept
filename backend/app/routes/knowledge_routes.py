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
    
    # Allow empty skills to fall through to populate unvisited conceptual paths.
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
    CORE_CONCEPTS = [
        "Variables", "Loops", "Conditionals", "Functions", 
        "Data Structures", "Recursion", "Error Handling", 
        "Object Oriented Programming"
    ]
    
    visited_concepts = [c["concept"] for c in concepts_learned]
    unvisited = [c for c in CORE_CONCEPTS if c not in visited_concepts]
    
    # Sort by holistic score ascending to find weakest
    sorted_concepts = sorted(concepts_learned, key=lambda x: x["score"])
    
    # Target unvisited first, then low scoring (< 70)
    weak_concepts = [str(c["concept"]) for c in sorted_concepts if int(str(c["score"])) < 70]
    
    # De-duplicate while preserving order
    target_concepts: List[str] = []
    for c in (unvisited + weak_concepts):
        if c not in target_concepts:
            target_concepts.append(c)
            
    # If perfect score and all core visited, fallback to DSA default
    if not target_concepts:
        target_concepts = ["Data Structures and Algorithms"]
        
    videos = get_learning_videos(target_concepts, max_total=5)
    
    return {
        "languages": languages_dict,
        "concepts_learned": sorted_concepts,
        "youtube_recommendations": videos
    }
