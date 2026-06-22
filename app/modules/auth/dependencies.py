import logging
from datetime import datetime, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.exceptions import AppException, ErrorCode
from app.infrastructure.db.database import get_db
from app.infrastructure.redis.service import SessionCache
from app.modules.auth.security import TokenService
from app.modules.auth.session_repository import UserSessionRepository
from app.modules.auth.sсhemas import AccessTokenPayload
from app.modules.auth.utils import create_session_data
from app.modules.users.user_repository import UserRepository

logger = logging.getLogger("teamboard")

security = HTTPBearer()


async def get_token_payload(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = TokenService.decode_access_token(token)
    request.state.user_id = payload.sub_str
    return payload


async def verify_session(payload: AccessTokenPayload = Depends(get_token_payload), db: AsyncSession = Depends(get_db)):
    session_redis = await SessionCache.get(session_id=payload.sid_str)

    if session_redis is None:
        session_db = await UserSessionRepository.get_by_session_id(db=db, session_id=payload.sid)

        if not session_db:
            logger.warning("Session not found", extra={"event": "session_not_found"})
            raise AppException("Unauthorized", 401, ErrorCode.UNAUTHORIZED)

        if session_db.revoked_at is not None:
            logger.warning("Session revoked", extra={"event": "session_revoked"})
            raise AppException("Unauthorized", 401, ErrorCode.UNAUTHORIZED)

        if session_db.expires_at < datetime.now(timezone.utc):
            raise AppException("Unauthorized", 401, ErrorCode.UNAUTHORIZED)

        data_session = create_session_data(session_db)

        ttl_sec = settings.security.access_token_expire_seconds

        await SessionCache.set(session_id=str(session_db.session_id), data=data_session, ttl=ttl_sec)

    return payload


async def get_current_user(payload: AccessTokenPayload = Depends(verify_session), db: AsyncSession = Depends(get_db)):

    public_id = payload.sub_str

    user = await UserRepository.get_by_public_id(db, public_id)

    if not user or not user.is_active:
        raise AppException("Unauthorized", 401, ErrorCode.UNAUTHORIZED)

    return user
