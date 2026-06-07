from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User

class UserRepository:

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_public_id(db: AsyncSession, public_id: str) -> User | None:
        result = await db.execute(
            select(User).where(User.public_id == public_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_login(db: AsyncSession, login: str) -> User | None:

        result = await db.execute(
            select(User).where(
                or_(
                    User.email == login,
                    User.username == login
                )
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.flush()
        return user