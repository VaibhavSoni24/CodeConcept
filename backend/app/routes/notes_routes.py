from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Note, User
from ..services.auth_service import get_current_user
from pydantic import BaseModel

router = APIRouter(tags=["notes"])

class CreateNoteRequest(BaseModel):
    submission_id: int
    content: str

@router.get("/users/{user_id}/notes")
def get_notes(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notes = db.query(Note).filter(Note.user_id == user_id).all()
    return [{"id": n.id, "submission_id": n.analysis_id, "content": n.content, "timestamp": n.timestamp.isoformat()} for n in notes]

@router.post("/notes")
def create_note(payload: CreateNoteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_note = Note(user_id=current_user.id, analysis_id=payload.submission_id, content=payload.content)
    db.add(new_note)
    db.commit()
    return {"status": "success", "note_id": new_note.id}
