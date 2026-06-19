from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import User
from app.modules.users.user_repository import UserRepository
from app.modules.users.schema import UserSearchResponse


class UserService:

    @staticmethod
    async def search_users(db: AsyncSession,query: str, user: User) -> list[UserSearchResponse]:
        users = await UserRepository.search_by_username(db=db,query=query, current_user=user)

        return [UserSearchResponse(username=user.username) for user in users ]