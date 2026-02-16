from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.db.models.user import UserRole


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(UserBase):
    id: int
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

