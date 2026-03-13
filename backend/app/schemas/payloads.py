from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SubmitCodeRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    language: str = Field(default="python")
    code: str = Field(..., min_length=1)


class RunCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)


# --- Auth schemas ---
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    level: str = "beginner"


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=1)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str


class UserOut(BaseModel):
    id: int
    name: str
    email: Optional[str]
    level: str
    created_at: datetime

    model_config = {"from_attributes": True}
