from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid6 import uuid7

from app.infrastructure.db.base import Base


def now_dt():
    return datetime.now(timezone.utc)


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id: Mapped[int] = mapped_column(primary_key=True)

    public_id: Mapped[PyUUID] = mapped_column(
        PG_UUID(as_uuid=True), unique=True, nullable=False, default=uuid7, index=True
    )

    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(100), nullable=False)

    position: Mapped[int] = mapped_column(nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_dt, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_dt, onupdate=now_dt, nullable=False
    )

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    board: Mapped["Board"] = relationship("Board", back_populates="columns")

    cards: Mapped[list["Card"]] = relationship(
        "Card", back_populates="column", cascade="all, delete-orphan", order_by="Card.position"
    )
