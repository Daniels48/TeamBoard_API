from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.infrastructure.db.models.user_session import UserSession


def now_dt():
    return datetime.now(timezone.utc)


class UserSessionRepository:

    @staticmethod
    async def create(db: AsyncSession, session: UserSession) -> UserSession:
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def get_by_session_id(db: AsyncSession,session_id: UUID,) -> UserSession | None:
        result = await db.execute(
            select(UserSession).where(UserSession.session_id == session_id)
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
    async def revoke_all_sessions(db: AsyncSession,user_id: int) -> list[UUID]:
        result = await db.execute(
            select(UserSession.session_id).where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
        )

        session_ids = list(result.scalars().all())

        if not session_ids:
            return []

        stmt = (
            update(UserSession)
            .where(UserSession.session_id.in_(session_ids))
            .values(revoked_at=now_dt())
        )

        await db.execute(stmt)

        return session_ids

    @staticmethod
    async def get_active_by_user_id(db: AsyncSession, user_id: int) -> list[UserSession]:
        result = await db.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now_dt(),
            )
            .order_by(UserSession.last_used_at.desc())
        )

        return list(result.scalars().all())


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
    async def update_last_used(db: AsyncSession,session_id: UUID) -> None:
        await db.execute(
            update(UserSession)
            .where(UserSession.session_id == session_id)
            .values(last_used_at=now_dt())
        )

