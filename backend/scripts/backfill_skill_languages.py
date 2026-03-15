"""Backfill ConceptSkill language-wise stats from historical submissions.

Usage:
  python scripts/backfill_skill_languages.py --dry-run
  python scripts/backfill_skill_languages.py --apply
  python scripts/backfill_skill_languages.py --apply --user-id 3
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys
import os
from typing import Iterable

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")


def _normalize_database_url() -> None:
    """Resolve relative sqlite paths against backend root.

    Example:
      sqlite:///./codeconcept_new.db -> sqlite:///D:/.../backend/codeconcept_new.db
    """
    db_url = (os.getenv("DATABASE_URL") or "").strip().strip('"').strip("'")
    if not db_url.startswith("sqlite:///"):
        return

    raw_path = db_url[len("sqlite:///"):]
    if not raw_path:
        return

    db_path = Path(raw_path)
    if db_path.is_absolute():
        return

    abs_path = (BASE_DIR / db_path).resolve()
    os.environ["DATABASE_URL"] = f"sqlite:///{abs_path.as_posix()}"


_normalize_database_url()

from app.database import SessionLocal
from app.models import Submission, ConceptSkill
from app.services.profile_service import update_skill_scores


def _canonical_language(language: str) -> str:
    lang = (language or "python").lower().strip()
    if lang in {"js", "node"}:
        return "javascript"
    if lang in {"c++", "cxx", "cc"}:
        return "cpp"
    if lang in {"rs"}:
        return "rust"
    return lang


def _iter_submissions(db, user_id: int | None) -> Iterable[Submission]:
    q = db.query(Submission)
    if user_id is not None:
        q = q.filter(Submission.user_id == user_id)
    return q.order_by(Submission.timestamp.asc(), Submission.id.asc()).all()


def _extract_payload(submission: Submission):
    analysis = submission.analysis_result or {}
    concepts = analysis.get("concepts_detected") or []
    mistakes = analysis.get("mistakes") or []

    concepts_detected = [c for c in concepts if isinstance(c, str) and c.strip()]
    error_concepts = []
    for m in mistakes:
        concept = (m or {}).get("concept")
        if isinstance(concept, str) and concept.strip():
            error_concepts.append(concept.lower())

    return concepts_detected, error_concepts


def run_backfill(apply: bool, user_id: int | None):
    db = SessionLocal()
    try:
        submissions = list(_iter_submissions(db, user_id))
        if not submissions:
            print("No submissions found for selected scope.")
            return

        target_users = {s.user_id for s in submissions}
        print(f"Found {len(submissions)} submissions across {len(target_users)} user(s).")

        if not apply:
            print("Dry run only. No DB changes were made.")
            return

        # Rebuild ConceptSkill rows from scratch for deterministic backfill.
        skill_q = db.query(ConceptSkill)
        if user_id is not None:
            skill_q = skill_q.filter(ConceptSkill.user_id == user_id)
        deleted = skill_q.delete(synchronize_session=False)
        print(f"Deleted {deleted} existing ConceptSkill rows in scope.")

        updated_rows = 0
        for sub in submissions:
            concepts_detected, error_concepts = _extract_payload(sub)
            if not concepts_detected:
                continue

            update_skill_scores(
                db=db,
                user_id=sub.user_id,
                concepts_detected=concepts_detected,
                error_concepts=error_concepts,
                language=_canonical_language(sub.language),
            )
            updated_rows += 1

        db.commit()
        print(f"Backfill completed. Recomputed skills from {updated_rows} submissions.")

        final_q = db.query(ConceptSkill)
        if user_id is not None:
            final_q = final_q.filter(ConceptSkill.user_id == user_id)
        print(f"ConceptSkill rows now: {final_q.count()}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill ConceptSkill language-wise stats")
    parser.add_argument("--apply", action="store_true", help="Apply DB updates")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only; no DB writes")
    parser.add_argument("--user-id", type=int, default=None, help="Limit to one user id")
    args = parser.parse_args()

    should_apply = bool(args.apply) and not bool(args.dry_run)
    print(f"[{datetime.utcnow().isoformat()}] Starting backfill")
    run_backfill(apply=should_apply, user_id=args.user_id)
