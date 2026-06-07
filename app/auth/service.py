import logging
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import create_session_data
from app.auth.security import PasswordService, TokenService
from app.auth.utils import parse_user_agent
from app.core.Exceptions.exceptions import AppException, ErrorCode
from app.core.config import settings
from app.db.models import User, UserSession
from app.db.repositories.session_repository import UserSessionRepository
from app.db.repositories.user_repository import UserRepository
from app.core.redis_service import SessionCache

logger = logging.getLogger("teamboard")

class AuthService:
    def __init__ (
        self,
        password_service: PasswordService = PasswordService(),
        token_service: TokenService = TokenService()
    ):
        self.password_service = password_service
        self.token_service = token_service

    async def _create_session_and_tokens(self, db, user: User, request):

        refresh_token = self.token_service.generate_refresh_token()
        refresh_token_hash = self.token_service.hash_refresh_token(refresh_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.security.refresh_token_expire_days
        )

        device_info = parse_user_agent(request)

        session = UserSession(
            user_id=user.id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            device_name=device_info["device_name"],
            device_type=device_info["device_type"],
            browser=device_info["browser"],
            os=device_info["os"],
            ip_address=device_info["ip_address"],
            last_used_at=datetime.now(timezone.utc),
        )

        await UserSessionRepository.create(db, session)

        access_token = self.token_service.create_access_token(
            public_id=user.public_id,
            session_id=session.session_id,
            role=user.role.value,
        )

        data_session = create_session_data(session)

        await SessionCache.set(
            session_id=str(session.session_id),
            data=data_session,
            ttl=settings.security.refresh_token_expire_seconds
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    async def login(self, db, data, request):
        async with db.begin():
            user = await UserRepository.get_by_login(db, data.login)

            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            if not self.password_service.verify_password(data.password, user.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            tokens = await self._create_session_and_tokens(db, user, request)

            return tokens

    async def register(self, db, data, request):
        try:
            async with db.begin():

                hashed_password = self.password_service.hash_password(data.password)

                user = User(
                    username=data.username,
                    email=data.email,
                    hashed_password=hashed_password,
                    first_name=data.first_name,
                    last_name=data.last_name,
                )

                user = await UserRepository.create(db, user)
                tokens = await self._create_session_and_tokens(db, user, request)

        except IntegrityError as e:
            error = str(e.orig).lower()

            if "uq_users_email" in error:
                raise AppException(
                    message="Email already registered",
                    status_code=400,
                    code=ErrorCode.EMAIL_ALREADY_EXISTS,
                )

            if "uq_users_username" in error:
                raise AppException(
                    message="Username already taken",
                    status_code=400,
                    code=ErrorCode.USERNAME_TAKEN,
                )

            raise AppException(
                message="Registration error",
                status_code=400,
                code=ErrorCode.VALIDATION_ERROR,
            )

        return tokens


    async def refresh(self, db: AsyncSession, refresh_token: str) -> str:

        refresh_hash = self.token_service.hash_refresh_token(refresh_token)

        session = await UserSessionRepository.get_by_refresh_hash(db, refresh_hash)

        if not session:
            logger.warning(
                "Session not found in db",
                extra={"event": "session_not_found"},
            )
            raise AppException("Authorization", 401)

        if session.expires_at < datetime.now(timezone.utc):
            logger.warning(
                "Refresh token expired",
                extra={"event": "refresh_token_expired"},
            )
            raise AppException("Authorization", 401)

        if session.revoked_at is not None:
            logger.warning(
                "Session revoked",
                extra={"event": "session_revoked"},
            )
            raise AppException("Authorization", 401)


        user = await UserRepository.get_by_id(db, session.user_id)

        if not user or not user.is_active:
            logger.warning(
                "User not found",
                extra={"event": "user_not_found"},
            )
            raise AppException("Authorization", 401)

        access_token = self.token_service.create_access_token(
            public_id=user.public_id,
            session_id=session.session_id,
            role=user.role.value,
        )

        return access_token
