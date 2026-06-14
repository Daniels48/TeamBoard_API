from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories.user_repository import UserRepository
from app.users.schema import UserSearchResponse


class UserService:

    @staticmethod
    async def search_users(db: AsyncSession,query: str, user: User) -> list[UserSearchResponse]:
        users = await UserRepository.search_by_username(db=db,query=query, current_user=user)

        return [UserSearchResponse(username=user.username) for user in users ]