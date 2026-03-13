from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SubmitCodeRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    language: str = Field(default="python")
    code: str = Field(..., min_length=1)


class RunCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: Optional[str] = None
    level: str = "beginner"


class UserOut(BaseModel):
    id: int
    name: str
    email: Optional[str]
    level: str
    created_at: datetime

    model_config = {"from_attributes": True}
