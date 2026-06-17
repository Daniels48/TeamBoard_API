from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BoardColumnCreate(BaseModel):
    title: str


class BoardColumnResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    public_id: UUID
    title: str
    position: int

    created_at: datetime
    updated_at: datetime


class BoardColumnUpdate(BaseModel):
    title: str