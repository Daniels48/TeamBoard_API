from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.columns.schema import BoardColumnResponse
from app.cards.schema import CardResponse


class BoardCreate(BaseModel):
    title: str = Field(min_length=1,max_length=255)
    description: str | None = None


class BoardUpdate(BaseModel):
    title: str | None = Field( default=None, max_length=255)
    description: str | None = None


class BoardResponse(BaseModel):
    public_id: UUID
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    owner_username: str
    role: str

    columns_count: int
    cards_count: int

    model_config = ConfigDict(
        from_attributes=True
    )

class BoardBaseResponse(BaseModel):
    public_id: UUID
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

class ColumnFullResponse(BoardColumnResponse):
    cards: list[CardResponse]


class BoardFullResponse(BoardBaseResponse):
    board_role: str | None = None
    owner_username: str | None = None
    columns: list[ColumnFullResponse]