from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, verify_session
from app.auth.sсhemas import SessionCacheData
from app.core.redis_service import SessionCache
from app.users.schema import UserRead

router_users = APIRouter(prefix="/users", tags=["users"])


@router_users.get("/me", response_model=UserRead)
async def get_me(current_user=Depends(get_current_user)):
    return current_user

@router_users.get("/check", response_model=SessionCacheData)
async def get_user_data(payload = Depends(verify_session)):
    session = await SessionCache.get(payload.sid_str)
    return SessionCacheData.model_validate_json(session)