import json
import logging
from datetime import datetime, timezone, timedelta
from secrets import randbelow

from cryptography import fernet
from cryptography.fernet import InvalidToken
from fastapi import Request

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


def generate_confirmation_code():
    return str(randbelow(900000) + 100000)

def now_dt():
    return datetime.now(timezone.utc)


class AuthService:
    def __init__ (self):
        self.password_service = PasswordService()
        self.token_service = TokenService()

    async def _create_session_and_tokens(
            self,
            db: AsyncSession,
            user: User,
            request: Request,
    ) -> dict:

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
        user = await UserRepository.get_by_login(db, data.login)

        if not user:
            raise AppException("Invalid credentials", 401)

        if not self.password_service.verify_password(data.password, user.hashed_password):
            raise AppException("Invalid credentials", 401)

        tokens = await self._create_session_and_tokens(db, user, request)

        await db.commit()
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

    async def refresh(self, db: AsyncSession, refresh_token: str) -> dict[str, str]:

        refresh_hash = self.token_service.hash_refresh_token(refresh_token)

        session = await UserSessionRepository.get_by_refresh_hash(db, refresh_hash)

        if not session:
            logger.warning(
                "Session not found in db",
                extra={"event": "session_not_found"},
            )
            raise AppException(
                "Unauthorized",
                401,
            )
        if session.expires_at < datetime.now(timezone.utc):
            logger.warning(
                "Refresh token expired",
                extra={"event": "refresh_token_expired"},
            )
            raise AppException(
                "Unauthorized",
                401,
            )

        if session.revoked_at is not None:
            logger.warning(
                "Session revoked",
                extra={"event": "session_revoked"},
            )
            raise AppException(
                "Unauthorized",
                401,
            )


        user = await UserRepository.get_by_id(db, session.user_id)

        if not user or not user.is_active:
            logger.warning(
                "User not found",
                extra={"event": "user_not_found"},
            )
            raise AppException(
                "Unauthorized",
                401,
            )

        access_token = self.token_service.create_access_token(
            public_id=user.public_id,
            session_id=session.session_id,
            role=user.role.value,
        )

        return {"access_token": access_token}

    @staticmethod
    async def generate_email_verification(db: AsyncSession,user: User) -> str:
        code = generate_confirmation_code()
        user.email_verification_token = code
        user.email_verification_token_expires_at = now_dt() + timedelta(hours=24)

        await db.commit()

        return code

    @staticmethod
    async def verify_email(db: AsyncSession,user: User, code: str,) -> dict[str, str]:
        if user.is_verified:
            raise AppException(
                "Email already verified",
                400,
            )
        if not user.email_verification_token_valid:
            raise AppException(
                "Verification code expired",
                400,
            )

        if user.email_verification_token != code:
            raise AppException(
                "Invalid verification code",
                400,
            )

        user.email_verified_at = now_dt()

        user.email_verification_token = None
        user.email_verification_token_expires_at = None

        await db.commit()

        return {"message": "Email verified successfully"}

    @staticmethod
    async def generate_password_reset(db: AsyncSession,user: User) -> str:
        code = generate_confirmation_code()
        user.password_reset_token = code
        user.password_reset_token_expires_at = now_dt() + timedelta(minutes=15)

        await db.commit()

        return code

    @staticmethod
    async def verify_reset_code(db: AsyncSession,email: str,code: str) -> None:
        user = await UserRepository.get_by_email(db=db, email=email,)

        if not user:
            raise AppException(
                "Invalid code",
                400,
            )

        if not user.password_reset_token_valid:
            raise AppException(
                "Code expired",
                400,
            )

        if user.password_reset_token != code:
            raise AppException(
                "Invalid code",
                400,
            )

    async def reset_password(
            self,
            db: AsyncSession,
            token: str,
            new_password: str,
    ) -> None:
        try:
            payload = PasswordResetService().decrypt(token)
        except InvalidToken:
            raise AppException("Invalid reset token", 400)
        email = payload["email"]
        code = payload["code"]

        user = await UserRepository.get_by_email(db=db,email=email,)

        if not user:
            raise AppException(
                "Invalid reset token",
                400,
            )

        if not user.password_reset_token_valid:
            raise AppException(
                "Reset code expired",
                400,
            )

        if user.password_reset_token != code:
            raise AppException(
                "Invalid reset token",
                400,
            )

        user.hashed_password = self.password_service.hash_password(new_password)

        user.password_changed_at = now_dt()

        user.password_reset_token = None
        user.password_reset_token_expires_at = None

        await UserSessionRepository.revoke_all_session(db=db, user_id=user.id)

        await db.commit()


class PasswordResetService:
    def __init__(self) -> None:
        self.fernet = fernet.Fernet(settings.security.password_reset_key)


    def encrypt(self,data: dict,) -> str:
        payload = json.dumps(data)
        return self.fernet.encrypt(payload.encode()).decode()

    def decrypt(self, token: str) -> dict:
        payload = self.fernet.decrypt(token.encode()).decode()
        return json.loads(payload)