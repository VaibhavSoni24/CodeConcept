import os
import sys
import tempfile
import subprocess
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()  # Load .env BEFORE any os.getenv() calls

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import User, Submission, ConceptError
from .schemas.payloads import (
    SubmitCodeRequest, RunCodeRequest, CreateUserRequest, UserOut,
    RegisterRequest, LoginRequest, TokenOut,
)
from .services.auth_service import hash_password, verify_password, create_token

# Existing services
from .services.static_analyzer import run_static_analysis
from .services.concept_rules import load_rules
from .services.diagnostic_ai import generate_diagnostic_with_ai
from .services.profile_service import (
    update_learning_profile,
    get_profile_summary,
    update_skill_scores,
    get_skill_scores,
)

# New analysis modules
from .services.misconception_detector import detect_misconceptions
from .services.smell_analyzer import detect_code_smells
from .services.complexity_analyzer import analyze_complexity
from .services.concept_detector import detect_concepts
from .services.execution_tracer import run_execution_trace
from .services.flow_graph import build_flow_graph

Base.metadata.create_all(bind=engine)
rules = load_rules()

app = FastAPI(title="CodeConcept MVP", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- Auth endpoints ---

@app.post("/auth/register", response_model=TokenOut)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        level=payload.level,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.email)
    return TokenOut(access_token=token, user_id=user.id, name=user.name, email=user.email)


@app.post("/auth/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token = create_token(user.id, user.email)
    return TokenOut(access_token=token, user_id=user.id, name=user.name, email=user.email)


@app.post("/users", response_model=UserOut)
def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)):
    user = User(name=payload.name, email=payload.email, level=payload.level)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/profiles/{user_id}")
def profile(user_id: int, db: Session = Depends(get_db)):
    summary = get_profile_summary(db, user_id)
    skill_scores = get_skill_scores(db, user_id)
    return {"user_id": user_id, "profiles": summary, "skill_scores": skill_scores}


@app.post("/run-code")
def run_code(payload: RunCodeRequest):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(payload.code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [sys.executable, "-I", tmp_path],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Execution timed out after 2 seconds.", "exit_code": -1}
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@app.post("/trace")
def trace_code(payload: RunCodeRequest):
    """Return step-by-step execution trace for the given code."""
    trace = run_execution_trace(payload.code)
    return {"trace": trace}


@app.post("/submit-code")
def submit_code(payload: SubmitCodeRequest, db: Session = Depends(get_db)):
    if payload.language.lower() != "python":
        raise HTTPException(status_code=400, detail="MVP supports Python only.")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Create user first.")

    # --- Run all analyzers ---
    analysis = run_static_analysis(payload.code)
    misconceptions = detect_misconceptions(payload.code) if analysis["syntax"] == "ok" else []
    code_smells = detect_code_smells(payload.code) if analysis["syntax"] == "ok" else []
    complexity = analyze_complexity(payload.code)
    concepts_detected = detect_concepts(payload.code) if analysis["syntax"] == "ok" else []
    flow_graph = build_flow_graph(payload.code) if analysis["syntax"] == "ok" else {"nodes": [], "edges": [], "mermaid": ""}

    # Map issues from AST flags + misconceptions
    issues = map_analysis_to_issues(analysis, misconceptions)

    # AI diagnostics + refactoring suggestions
    ai_context = {
        "student_code": payload.code,
        "error_logs": analysis.get("syntax_error") or {},
        "ast_analysis": analysis,
        "student_history": get_profile_summary(db, payload.user_id),
    }
    diagnostic = generate_diagnostic_with_ai(ai_context, issues[0], code_smells)

    # Persist submission
    submission = Submission(
        user_id=payload.user_id,
        code=payload.code,
        language=payload.language,
        result=diagnostic.get("mistake_type", "analysis_completed"),
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
    update_learning_profile(db, payload.user_id, [i for i in issues if i.get("mistake_type") != "none"], concepts_detected)
    update_skill_scores(db, payload.user_id, concepts_detected, error_concepts)
    db.commit()

    # Ensure refactoring_suggestions is a list
    ref_sugg = diagnostic.get("refactoring_suggestions", [])
    if isinstance(ref_sugg, str):
        ref_sugg = [ref_sugg]
    elif not isinstance(ref_sugg, list):
        ref_sugg = []

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
        "refactoring_suggestions": ref_sugg,

        # New analysis data
        "misconceptions": misconceptions,
        "code_smells": code_smells,
        "complexity": complexity,
        "concepts_detected": concepts_detected,
        "flow_graph": flow_graph,

        # Profile data
        "profile": get_profile_summary(db, payload.user_id),
        "skill_scores": get_skill_scores(db, payload.user_id),
    }
