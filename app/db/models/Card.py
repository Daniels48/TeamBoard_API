from datetime import datetime, timezone
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from app.db.base import Base

def now_dt():
    return datetime.now(timezone.utc)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    public_id: Mapped[PyUUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid7,
        index=True
    )

    column_id: Mapped[int] = mapped_column(
        ForeignKey("board_columns.id"),
        nullable=False,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    position: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_dt,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_dt,
        onupdate=now_dt,
        nullable=False
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    column: Mapped["BoardColumn"] = relationship(
        "BoardColumn",
        back_populates="cards"
    )