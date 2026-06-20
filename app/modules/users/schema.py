from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID as PyUUID
from app.infrastructure.db.models.user import UserRole


class UserSearchResponse(BaseModel):
    username: str


class UpdateProfileRequest(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None

class UserRead(BaseModel):
    public_id: PyUUID
    username: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
