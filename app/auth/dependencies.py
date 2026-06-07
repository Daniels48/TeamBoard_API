import logging
from datetime import datetime, timezone

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import TokenService
from app.auth.service import AuthService
from app.auth.sсhemas import AccessTokenPayload
from app.auth.utils import create_session_data
from app.core.Exceptions.exceptions import AppException, ErrorCode
from app.core.config import settings
from app.core.observability.context import user_id_ctx
from app.core.redis_service import SessionCache
from app.db.database import get_db
from app.db.repositories.session_repository import UserSessionRepository
from app.db.repositories.user_repository import UserRepository


logger = logging.getLogger("teamboard")

security = HTTPBearer()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_auth_service():
    return AuthService()


async def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = TokenService().decode_access_token(token)
    user_id_ctx.set(payload.sub_str)
    return payload


async def verify_session(
    payload: AccessTokenPayload = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db)):

    session_redis = await SessionCache.get(session_id=payload.sid_str)

    if session_redis is None:
        session_db = await UserSessionRepository.get_by_session_id(db=db, session_id=payload.sid)

        if not session_db:
            logger.warning(
                "Session not found",
                extra={"event": "session_not_found"}
            )
            raise AppException("Unauthorized", 401, ErrorCode.SESSION_NOT_FOUND)

        if session_db.revoked_at is not None:
            logger.warning(
                "Session revoked",
                extra={"event": "session_revoked"}
            )
            raise AppException("Unauthorized", 401, ErrorCode.SESSION_REVOKED)

        if session_db.expires_at < datetime.now(timezone.utc):
            raise AppException("Unauthorized", 401, ErrorCode.SESSION_EXPIRED)

        data_session = create_session_data(session_db)

        ttl_sec = settings.security.access_token_expire_seconds

        await SessionCache.set(session_id=str(session_db.session_id), data=data_session, ttl=ttl_sec)

    return payload


async def get_current_user(
    payload: AccessTokenPayload = Depends(verify_session),
    db: AsyncSession = Depends(get_db),
):

    public_id = payload.sub_str

    user = await UserRepository.get_by_public_id(db, public_id)

    if not user:
        raise AppException("Unauthorized", 401, ErrorCode.USER_NOT_FOUND)

    if not user.is_active:
        raise AppException("Unauthorized", 401, ErrorCode.USER_NOT_ACTIVE)

    return user
