from fastapi import APIRouter, Depends

from app.auth.dependencies import verify_session
from app.auth.sсhemas import SessionCacheData
from app.core.dependencies import CurrentUser, DBSession
from app.core.redis_service import SessionCache

from app.users.schema import UserRead, UserSearchResponse
from app.users.service import UserService

router_users = APIRouter(prefix="/users", tags=["users"])


@router_users.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    return current_user

@router_users.get("/check", response_model=SessionCacheData)
async def get_user_data(payload = Depends(verify_session)):
    session = await SessionCache.get(payload.sid_str)
    return SessionCacheData.model_validate_json(session)

@router_users.get("/search",response_model=list[UserSearchResponse])
async def search_users(q: str, db: DBSession, user: CurrentUser):
    if len(q.strip()) < 2:
        return []

    return await UserService.search_users(db=db, query=q, user=user)