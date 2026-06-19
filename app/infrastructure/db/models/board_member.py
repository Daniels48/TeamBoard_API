from datetime import datetime, timezone

from enum import StrEnum

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Enum

from app.infrastructure.db.base import Base


def now_dt():
    return datetime.now(timezone.utc)



class BoardRole(StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"



class BoardMember(Base):
    __tablename__ = "board_members"

    board_id: Mapped[int] = mapped_column(
        ForeignKey("boards.id"),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True,
    )

    role: Mapped[BoardRole] = mapped_column(
        Enum(BoardRole),
        nullable=False,
        default=BoardRole.VIEWER,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_dt,
        nullable=False,
    )

    board: Mapped["Board"] = relationship(
        "Board",
        back_populates="members",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="board_members",
    )