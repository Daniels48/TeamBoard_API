from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.user_session import UserSession


def now_dt():
    return datetime.now(timezone.utc)


class UserSessionRepository:

    @staticmethod
    async def create(db: AsyncSession, session: UserSession) -> UserSession:
        db.add(session)
        await db.flush()
        # await db.commit()  # ✅ Фиксируем транзакцию
        # await db.refresh(session)  # Обновляем объект после коммита
        return session

    @staticmethod
    async def get_by_session_id(db: AsyncSession, session_id: UUID) -> UserSession | None:
        result = await db.execute(
            select(UserSession)
            .options(joinedload(UserSession.user))
            .where(UserSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_refresh_hash(db: AsyncSession, refresh_hash: str) -> UserSession | None:
        result = await db.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == refresh_hash
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_all(db: AsyncSession, user_id: int) -> None:
        stmt = (
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None)
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )

        await db.execute(stmt)

    @staticmethod
    async def get_active_by_user_id(db: AsyncSession,user_id: int):
        result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(False),
                UserSession.expires_at > now_dt()
            )
        )
        return result.scalars().all()

    @staticmethod
    async def revoke_session(
        db: AsyncSession,
        session_id: UUID
    ) -> None:
        await db.execute(
            update(UserSession)
            .where(UserSession.session_id == session_id)
            .values(
                is_revoked=True,
                revoked_at=now_dt()
            )
        )

    @staticmethod
    async def revoke_all_for_user(
        db: AsyncSession,
        user_id: int
    ) -> None:
        await db.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.is_revoked.is_(False)
            )
            .values(
                is_revoked=True,
                revoked_at=now_dt()
            )
        )

    @staticmethod
    async def update_last_used(
        db: AsyncSession,
        session_id: UUID
    ) -> None:
        await db.execute(
            update(UserSession)
            .where(UserSession.session_id == session_id)
            .values(last_used_at=now_dt())
        )