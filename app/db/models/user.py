from datetime import datetime, timezone
from enum import Enum
from uuid6 import uuid7
from uuid import UUID as PyUUID

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, Enum as SqlEnum


from app.db.base import Base

from typing import TYPE_CHECKING



if TYPE_CHECKING:
    from app.db.models import UserSession


def now_dt():
    return datetime.now(timezone.utc)



class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    public_id: Mapped[PyUUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid7,
        index=True
    )

    username: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role"), default=UserRole.USER, nullable=False)

    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_dt, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=now_dt, onupdate=now_dt, nullable=False)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)

    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    boards: Mapped[list["Board"]] = relationship(
        "Board",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    email_verification_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    email_verification_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    password_reset_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    password_reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    board_members: Mapped[list["BoardMember"]] = relationship(
        "BoardMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    @property
    def is_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def email_verification_token_valid(self) -> bool:
        return (
                self.email_verification_token is not None
                and self.email_verification_token_expires_at is not None
                and self.email_verification_token_expires_at > now_dt()
        )

    @property
    def password_reset_token_valid(self) -> bool:
        return (
                self.password_reset_token is not None
                and self.password_reset_token_expires_at is not None
                and self.password_reset_token_expires_at > now_dt()
        )