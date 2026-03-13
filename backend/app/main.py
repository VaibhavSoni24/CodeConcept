import os
import sys
import tempfile
import subprocess
from typing import Dict, Any, List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import User, Submission, ConceptError
from .schemas.payloads import SubmitCodeRequest, RunCodeRequest, CreateUserRequest, UserOut
from .services.static_analyzer import run_static_analysis
from .services.concept_rules import load_rules
from .services.diagnostic_ai import generate_diagnostic_with_ai
from .services.profile_service import update_learning_profile, get_profile_summary

Base.metadata.create_all(bind=engine)
rules = load_rules()

app = FastAPI(title="CodeConcept MVP", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def map_analysis_to_issues(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    if analysis["syntax"] == "error":
        message = analysis["syntax_error"]["message"].lower()
        key = "missing_colon" if "expected ':'" in message or "expected :" in message else "missing_colon"
        issue = rules.get(key, {})
        issue = {**issue, "mistake_id": key}
        issues.append(issue)
        return issues

    for flag in analysis.get("ast_flags", []):
        issue = rules.get(flag["mistake_id"], {})
        if issue:
            issues.append({**issue, "mistake_id": flag["mistake_id"], "detail": flag.get("detail")})

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
    return {"user_id": user_id, "profiles": summary}


@app.post("/run-code")
def run_code(payload: RunCodeRequest):
    # MVP sandbox: isolated python mode and short timeout to reduce risk.
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


@app.post("/submit-code")
def submit_code(payload: SubmitCodeRequest, db: Session = Depends(get_db)):
    if payload.language.lower() != "python":
        raise HTTPException(status_code=400, detail="MVP supports Python only.")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Create user first.")

    analysis = run_static_analysis(payload.code)
    issues = map_analysis_to_issues(analysis)

    ai_context = {
        "student_code": payload.code,
        "error_logs": analysis.get("syntax_error") or {},
        "ast_analysis": analysis,
        "student_history": get_profile_summary(db, payload.user_id),
    }
    diagnostic = generate_diagnostic_with_ai(ai_context, issues[0])

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

    update_learning_profile(db, payload.user_id, [issue for issue in issues if issue.get("mistake_type") != "none"])
    db.commit()

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
        "profile": get_profile_summary(db, payload.user_id),
    }
