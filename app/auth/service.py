from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user import User
from app.auth.security import hash_password, verify_password, create_access_token


class AuthService:

    @staticmethod
    async def register_user(db: AsyncSession, data):
        result = await db.execute(
            select(User).where(User.email == data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User with this email already exists")

        new_user = User(
            username=data.username,
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            hashed_password=hash_password(data.password),
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user
