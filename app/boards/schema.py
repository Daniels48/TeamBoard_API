from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.columns.schema import BoardColumnResponse
from app.cards.schema import CardResponse


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


class ColumnFullResponse(BoardColumnResponse):
    cards: list[CardResponse]


class BoardFullResponse(BoardResponse):
    board_role: str | None = None
    columns: list[ColumnFullResponse]