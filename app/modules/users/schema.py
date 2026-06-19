from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from uuid import UUID as PyUUID
from app.infrastructure.db.models.user import UserRole


class UserSearchResponse(BaseModel):
    username: str
    

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None


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

class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str