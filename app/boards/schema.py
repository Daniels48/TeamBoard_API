from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class BoardCreate(BaseModel):
    title: str = Field(min_length=1,max_length=255)
    description: str | None = None
    is_public: bool = False


class BoardUpdate(BaseModel):
    title: str | None = Field( default=None, max_length=255)
    description: str | None = None
    is_public: bool | None = None


class BoardResponse(BaseModel):
    public_id: UUID
    title: str
    description: str | None
    is_public: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )