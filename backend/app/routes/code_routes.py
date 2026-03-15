import os
import sys
import tempfile
import subprocess
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Submission, ConceptError
from ..schemas.payloads import SubmitCodeRequest, RunCodeRequest
from ..services.auth_service import get_current_user

# Existing services
from ..services.static_analyzer import run_static_analysis
from ..services.concept_rules import load_rules
from ..services.diagnostic_ai import generate_diagnostic_with_ai
from ..services.profile_service import (
    update_learning_profile,
    get_profile_summary,
    update_skill_scores,
    get_skill_scores,
)

# New analysis modules
from ..services.misconception_detector import detect_misconceptions
from ..services.smell_analyzer import detect_code_smells
from ..services.complexity_analyzer import analyze_complexity
from ..services.concept_detector import detect_concepts
from ..services.execution_tracer import run_execution_trace
from ..services.flow_graph import build_flow_graph
from ..services.analysis_service import dispatch_analysis

from ..services.execution_service import execute_code
from ..services.formatting_service import parse_and_format_code

router = APIRouter(tags=["code"])
rules = load_rules()


def map_analysis_to_issues(analysis: Dict[str, Any], misconceptions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    if analysis["syntax"] == "error":
        message = analysis["syntax_error"]["message"].lower()
        key = "missing_colon" if "expected ':'" in message or "expected :" in message else "missing_colon"
        issue = rules.get(key, {})
        issue = {**issue, "mistake_id": key}
        issues.append(issue)
        return issues

    # Map AST flags
    for flag in analysis.get("ast_flags", []):
        issue = rules.get(flag["mistake_id"], {})
        if issue:
            issues.append({**issue, "mistake_id": flag["mistake_id"], "detail": flag.get("detail")})

    # Map misconceptions
    for mis in misconceptions:
        mid = mis.get("misconception_id", "")
        issue = rules.get(mid, {})
        if issue and not any(i.get("mistake_id") == mid for i in issues):
            issues.append({**issue, "mistake_id": mid, "detail": mis.get("detail")})

    if not issues:
        issues.append(
            {
                "mistake_id": "no_major_issues",
                "concept": "Foundational coding flow",
                "mistake_type": "none",
                "hint_1": "Good work. Try adding tests for edge cases.",
                "hint_2": "Consider readability improvements such as naming.",
                "hint_3": "Try a more advanced variation of the same task.",
                "explanation": "No major conceptual issues detected in this submission.",
                "practice": "Create two edge-case tests and verify expected output.",
            }
        )

    return issues


@router.post("/run-code")
def run_code(payload: RunCodeRequest, _current_user: User = Depends(get_current_user)):
    return execute_code(payload.language, payload.code)

@router.post("/format-code")
def format_code(payload: RunCodeRequest, _current_user: User = Depends(get_current_user)):
    formatted_code, error = parse_and_format_code(payload.language, payload.code)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"code": formatted_code}


@router.post("/trace")
def trace_code(payload: RunCodeRequest, _current_user: User = Depends(get_current_user)):
    """Return step-by-step execution trace for the given code (all languages)."""
    trace = run_execution_trace(payload.code, payload.language)
    return {"trace_available": True, "trace": trace}


@router.post("/submit-code")
def submit_code(payload: SubmitCodeRequest, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Create user first.")

    COST_PER_ANALYSIS = 5
    if user.credits < COST_PER_ANALYSIS:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please recharge from the shop."
        )

    # --- Run all analyzers via language dispatcher ---
    try:
        analysis_data = dispatch_analysis(payload.language, payload.code)
        
        analysis = analysis_data["analysis"]
        misconceptions = analysis_data["misconceptions"]
        code_smells = analysis_data["code_smells"]
        vulnerabilities = analysis_data.get("vulnerabilities", [])
        vulnerability_meta = analysis_data.get(
            "vulnerability_meta",
            {"engine": "semgrep", "status": "error", "message": "missing_meta"},
        )
        complexity = analysis_data["complexity"]
        concepts_detected = analysis_data["concepts_detected"]
        flow_graph = analysis_data["flow_graph"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code analysis failed: {str(e)}")

    issues = map_analysis_to_issues(analysis, misconceptions)

    # AI diagnostics + refactoring suggestions
    ai_context = {
        "student_code": payload.code,
        "language": payload.language,
        "error_logs": analysis.get("syntax_error") or {},
        "ast_analysis": analysis,
        "student_history": get_profile_summary(db, payload.user_id),
    }
    try:
        diagnostic = generate_diagnostic_with_ai(ai_context, issues[0], code_smells)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Diagnostic generation failed: {str(e)}")

    # ---- Compute confidence score ----
    # correct concepts = detected concepts that do NOT appear in the error set
    error_concept_set = set(
        i.get("concept", "").lower()
        for i in issues
        if i.get("mistake_type") != "none"
    )
    total_detected = len(concepts_detected)
    correct_count = sum(
        1 for c in concepts_detected if c.lower() not in error_concept_set
    )
    confidence = correct_count / max(total_detected, 1) if total_detected > 0 else (
        1.0 if not error_concept_set else 0.0
    )
    confidence = round(max(0.0, min(1.0, confidence)), 4)

    # ---- Build structured analysis_result (stored in DB + returned in response) ----
    analysis_result = {
        "confidence": confidence,
        "mistakes": [
            {
                "concept": i.get("concept", "Unknown"),
                "severity": i.get("difficulty", "medium"),
                "explanation": i.get("explanation", ""),
            }
            for i in issues
            if i.get("mistake_type") != "none"
        ],
        "concepts_detected": concepts_detected,
        "vulnerabilities": vulnerabilities,
        "vulnerability_meta": vulnerability_meta,
    }

    # Calculate code similarity
    from ..services.similarity_service import check_code_similarity
    similarity_score = check_code_similarity(db, user.id, payload.code, payload.language)

    # Persist submission
    submission = Submission(
        user_id=payload.user_id,
        code=payload.code,
        language=payload.language,
        result=diagnostic.get("mistake_type", "analysis_completed"),
        complexity=complexity,
        analysis_result=analysis_result,
    )
    db.add(submission)
    db.flush()

    for issue in issues:
        if issue.get("mistake_type") != "none":
            db.add(
                ConceptError(
                    submission_id=submission.id,
                    concept=issue.get("concept", "General Python fundamentals"),
                    error_type=issue.get("mistake_type", "Unknown"),
                    severity=issue.get("difficulty", "medium"),
                )
            )

    # Update profiles
    error_concepts = [i.get("concept", "").lower() for i in issues if i.get("mistake_type") != "none"]
    update_learning_profile(db, payload.user_id, [i for i in issues if i.get("mistake_type") != "none"])
    update_skill_scores(db, payload.user_id, concepts_detected, error_concepts)
    
    # Deduct credits
    user.credits -= COST_PER_ANALYSIS
    
    db.commit()

    # --- Build unified response ---
    return {
        "analysis": {
            "syntax": analysis["syntax"],
            "logic": issues[0].get("concept", "n/a"),
            "ast_flags": analysis.get("ast_flags", []),
        },
        "concept": diagnostic.get("concept_missed", issues[0].get("concept", "General Python fundamentals")),
        "mistake_type": diagnostic.get("mistake_type", issues[0].get("mistake_type", "unknown")),
        "hint_level_1": diagnostic.get("hint_1", issues[0].get("hint_1")),
        "hint_level_2": diagnostic.get("hint_2", issues[0].get("hint_2")),
        "hint_level_3": diagnostic.get("hint_3", issues[0].get("hint_3")),
        "explanation": diagnostic.get("explanation", issues[0].get("explanation")),
        "practice": diagnostic.get("practice", issues[0].get("practice")),
        "refactoring_suggestions": diagnostic.get("refactoring_suggestions", []),

        # New analysis data
        "misconceptions": misconceptions,
        "code_smells": code_smells,
        "vulnerabilities": vulnerabilities,
        "vulnerability_meta": vulnerability_meta,
        "complexity": complexity,
        "concepts_detected": concepts_detected,
        "flow_graph": flow_graph,
        "similarity_score": similarity_score,
        "analysis_result": analysis_result,
        "confidence": confidence,

        # Profile data
        "profile": get_profile_summary(db, payload.user_id),
        "skill_scores": get_skill_scores(db, payload.user_id),
        "remaining_credits": user.credits,
    }
