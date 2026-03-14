from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..services.auth_service import get_current_user

router = APIRouter(tags=["notes"])

# TODO: Add CRUD endpoints for notes on submissions
