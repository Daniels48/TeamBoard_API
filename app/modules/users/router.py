from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import verify_session
from app.modules.auth.sсhemas import SessionCacheData
from app.core.dependencies import CurrentUser, DBSession
from app.infrastructure.redis.service import SessionCache

from app.modules.users.schema import UserRead, UserSearchResponse, UpdateProfileRequest
from app.modules.users.service import UserService

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

@router_users.put("/profile", status_code=200)
async def update_profile(data: UpdateProfileRequest, db: DBSession,current_user: CurrentUser):
    user = await UserService.update_profile(db=db, user=current_user,data=data,)
    return user