from typing import Optional
from uuid import UUID

from pydantic import Field, BaseModel, EmailStr, field_serializer
from datetime import datetime

from app.db.models.user import UserRole


class UserLogin(BaseModel):
    login: str = Field(min_length=3)
    password: str = Field(min_length=6)


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionCacheData(BaseModel):
    public_id: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: UserRole


class AccessTokenPayload(BaseModel):
    sub: UUID
    sid: UUID
    role: str
    type: str = "access"
    iat: datetime
    exp: datetime

    @field_serializer("sub")
    def serialize_iat(self, sub: UUID):
        return str(sub)

    @field_serializer("sid")
    def serialize_sid(self, sid: UUID):
        return str(sid)

    @property
    def sub_str(self) -> str:
        return str(self.sub)

    @property
    def sid_str(self) -> str:
        return str(self.sid)


