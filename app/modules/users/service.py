from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.exceptions import AppException, ErrorCode
from app.infrastructure.db.models import User
from app.modules.users.schema import UpdateProfileRequest, UserSearchResponse
from app.modules.users.user_repository import UserRepository


class UserService:
    @staticmethod
    async def search_users(db: AsyncSession, query: str, user: User) -> list[UserSearchResponse]:
        users = await UserRepository.search_by_username(db=db, query=query, current_user=user)

        return [UserSearchResponse(username=user.username) for user in users]

    @staticmethod
    async def update_profile(db: AsyncSession, user: User, data: UpdateProfileRequest) -> User:

        if data.email is not None:
            user.email = data.email

        if data.first_name is not None:
            user.first_name = data.first_name

        if data.last_name is not None:
            user.last_name = data.last_name

        try:
            await UserRepository.update(db, user)

        except IntegrityError as e:
            error = str(e.orig).lower()

            if "uq_users_email" in error:
                raise AppException(
                    message="Email already registered", status_code=400, code=ErrorCode.EMAIL_ALREADY_EXISTS
                )

            raise AppException(message="Profile update failed", status_code=400)

        await db.commit()
        return user


class UserPolicy:
    @staticmethod
    def require_verified_email(user: User) -> None:
        if not user.is_verified:
            raise AppException("Email verification required", 403)
