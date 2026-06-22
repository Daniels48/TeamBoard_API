from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CardCreate(BaseModel):
    title: str
    description: str | None = None


class CardUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class CardPosition(BaseModel):
    card_id: UUID
    column_id: UUID
    position: int


class BoardLayoutUpdate(BaseModel):
    cards: list[CardPosition]


class CardMove(BaseModel):
    column_id: UUID
    position: int


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID

    title: str
    description: str | None

    position: int

    created_at: datetime
    updated_at: datetime
