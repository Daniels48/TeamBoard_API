import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from secrets import randbelow
from uuid import UUID

from cryptography import fernet
from cryptography.fernet import InvalidToken
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions.exceptions import AppException, ErrorCode
from app.infrastructure.db.models import User, UserSession
from app.infrastructure.redis.service import SessionCache
from app.modules.auth.security import PasswordService, TokenService
from app.modules.auth.session_repository import UserSessionRepository
from app.modules.auth.sсhemas import UserLogin, UserRegister
from app.modules.auth.utils import create_session_data
from app.modules.users.service import UserPolicy
from app.modules.users.user_repository import UserRepository

logger = logging.getLogger("teamboard")


def now_dt():
    return datetime.now(timezone.utc)


class AuthService:
    @staticmethod
    async def login(db: AsyncSession, data: UserLogin, device_info: dict) -> dict[str, str]:
        now = now_dt()
        user = await UserRepository.get_by_login(db, data.login)

        if not user:
            raise AppException("Invalid credentials", 401)

        user.last_login_at = now

        password_valid = PasswordService.verify_password(data.password, user.hashed_password)

        if not password_valid:
            raise AppException("Invalid credentials", 401)

        try:
            tokens, session = await AuthService._create_session_and_tokens(db, user, device_info, now)
            await db.commit()

        except Exception:
            await db.rollback()
            logger.exception("Unexpected login error", extra={"event": "login_failed"})
            raise

        await AuthService._try_cache_session(session)

        return tokens

    @staticmethod
    async def register(db: AsyncSession, data: UserRegister, device_info: dict) -> dict[str, str]:
        try:
            async with db.begin():
                hashed_password = PasswordService.hash_password(data.password)
                user = User(**data.model_dump(exclude={"password"}), hashed_password=hashed_password)
                user = await UserRepository.create(db, user)

                tokens, session = await AuthService._create_session_and_tokens(db, user, device_info, now_dt())

            await AuthService._try_cache_session(session)

            return tokens

        except IntegrityError as e:
            error = str(e.orig).lower()
            if "uq_users_email" in error:
                raise AppException(
                    message="Email already registered", status_code=400, code=ErrorCode.EMAIL_ALREADY_EXISTS
                )

            if "uq_users_username" in error:
                raise AppException(message="Username already taken", status_code=400, code=ErrorCode.USERNAME_TAKEN)

            logger.exception("Unknown registration integrity error", extra={"event": "registration_integrity_error"})
            raise AppException(message="Registration error", status_code=400)

        except AppException:
            raise

        except Exception:
            logger.exception("Unexpected registration error", extra={"event": "registration_failed"})
            raise

    @staticmethod
    async def refresh(db: AsyncSession, refresh_token: str) -> dict[str, str]:
        refresh_hash = TokenService.hash_refresh_token(refresh_token)
        session = await UserSessionRepository.get_by_refresh_hash(db, refresh_hash)

        now = now_dt()
        if not session or session.expires_at < now or session.revoked_at is not None:
            raise AppException("Unauthorized", 401)

        user = await UserRepository.get_by_id(db, session.user_id)

        if not user or not user.is_active:
            raise AppException("Unauthorized", 401)

        try:
            session.last_used_at = now
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception(
                "Failed to update session activity",
                extra={"event": "refresh_session_update_failed"},
            )
            raise

        access_token = TokenService.create_access_token(
            public_id=user.public_id,
            session_id=session.session_id,
            role=user.role.value,
        )

        return {"access_token": access_token}

    @staticmethod
    async def logout_all_sessions(db: AsyncSession, user_id: int) -> None:
        session_ids = await UserSessionRepository.revoke_all_sessions(db=db, user_id=user_id)

        await AuthService._commit(db, event="all_sessions_logged_out")

        for session_id in session_ids:
            try:
                await SessionCache.delete(str(session_id))
            except RedisError:
                logger.exception(
                    "Failed to remove revoked session from cache",
                    extra={
                        "event": "session_cache_delete_failed",
                        "session_id": str(session_id),
                    },
                )

    @staticmethod
    async def logout_current_session(db: AsyncSession, refresh_token: str | None) -> None:
        if not refresh_token:
            return

        refresh_hash = TokenService.hash_refresh_token(refresh_token)
        session = await UserSessionRepository.get_by_refresh_hash(db, refresh_hash)

        if not session:
            return

        session.revoked_at = now_dt()
        await AuthService._commit(db, event="current_session_logged_out")
        await AuthService._try_invalidate_session_cache(session.session_id)

    @staticmethod
    async def logout_session(db: AsyncSession, user_id: int, session_id: UUID) -> None:
        session = await UserSessionRepository.get_by_session_id(db=db, session_id=session_id)

        if not session or session.user_id != user_id:
            raise AppException(status_code=404, message="Session not found")

        if session.revoked_at is not None:
            return

        session.revoked_at = now_dt()

        await AuthService._commit(db, event="session_logged_out")
        await AuthService._try_invalidate_session_cache(session.session_id)

    @staticmethod
    async def create_email_verification_code(db: AsyncSession, user: User) -> str:
        if user.is_verified:
            raise AppException("Email already verified", 400)

        code = AuthService._generate_confirmation_code()

        user.email_verification_token = TokenService.hash_confirmation_code(code)
        user.email_verification_token_expires_at = now_dt() + timedelta(hours=24)

        await AuthService._commit(db, event="email_verification_code_created")

        return code

    @staticmethod
    async def verify_email(db: AsyncSession, user: User, code: str) -> dict[str, str]:
        if user.is_verified:
            raise AppException("Email already verified", 400)

        if not user.email_verification_token_valid:
            raise AppException("Verification code expired", 400)

        if not hmac.compare_digest(user.email_verification_token, TokenService.hash_confirmation_code(code)):
            raise AppException("Invalid email verification code", 400)

        user.email_verified_at = now_dt()
        user.email_verification_token = None
        user.email_verification_token_expires_at = None

        await AuthService._commit(db, event="email_verified")

        return {"message": "Email verified successfully"}

    @staticmethod
    async def create_password_reset_code(db: AsyncSession, user: User) -> str:
        UserPolicy.require_verified_email(user=user)
        code = AuthService._generate_confirmation_code()
        user.password_reset_token = TokenService.hash_confirmation_code(code)
        user.password_reset_token_expires_at = now_dt() + timedelta(minutes=15)

        await AuthService._commit(db, event="password_create_reset_code")

        return code

    @staticmethod
    async def verify_reset_code(db: AsyncSession, email: str, code: str) -> User:
        user = await UserRepository.get_by_email(db=db, email=email)

        if not user:
            raise AppException("Invalid password reset code", 400)

        if not user.password_reset_token_valid:
            raise AppException("Invalid password reset code", 400)

        if not hmac.compare_digest(user.password_reset_token, TokenService.hash_confirmation_code(code)):
            raise AppException("Invalid password reset code", 400)

        return user

    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
        try:
            payload = PasswordResetService.decrypt(token)
        except InvalidToken:
            raise AppException("Invalid reset token", 400)

        user = await AuthService.verify_reset_code(db, payload["email"], payload["code"])

        user.hashed_password = PasswordService.hash_password(new_password)
        user.password_changed_at = now_dt()
        user.password_reset_token = None
        user.password_reset_token_expires_at = None

        await AuthService.logout_all_sessions(db=db, user_id=user.id)

        await AuthService._commit(db, event="password_reset")

    @staticmethod
    async def _create_session_and_tokens(
        db: AsyncSession,
        user: User,
        device_info: dict,
        now: datetime,
    ) -> tuple[dict[str, str], UserSession]:

        new_refresh_token = TokenService.generate_refresh_token()

        new_session = UserSession(
            user_id=user.id,
            refresh_token_hash=TokenService.hash_refresh_token(new_refresh_token),
            expires_at=now + timedelta(days=settings.security.refresh_token_expire_days),
            last_used_at=now,
            **device_info,
        )

        new_session = await UserSessionRepository.create(db, new_session)

        new_access_token = TokenService.create_access_token(
            public_id=user.public_id,
            session_id=new_session.session_id,
            role=user.role.value,
        )

        return {"access_token": new_access_token, "refresh_token": new_refresh_token}, new_session

    @staticmethod
    async def _try_cache_session(session: UserSession) -> None:
        try:
            session_data = create_session_data(session)

            await SessionCache.set(
                session_id=str(session.session_id),
                data=session_data,
                ttl=settings.security.refresh_token_expire_seconds,
            )

        except RedisError:
            logger.exception("Failed to cache session after commit", extra={"event": "session_cache_failed"})

    @staticmethod
    async def _try_invalidate_session_cache(session_id: UUID) -> None:
        try:
            await SessionCache.delete(str(session_id))
        except RedisError:
            logger.exception(
                "Failed to remove logged out session from cache",
                extra={
                    "event": "session_cache_delete_failed",
                    "session_id": str(session_id),
                },
            )

    @staticmethod
    async def _commit(db: AsyncSession, event: str) -> None:
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Database commit failed", extra={"event": event})
            raise

    @staticmethod
    def _generate_confirmation_code():
        return str(randbelow(900000) + 100000)


class PasswordResetService:
    fernet = fernet.Fernet(settings.security.password_reset_key)

    @classmethod
    def encrypt(cls, data: dict) -> str:
        payload = json.dumps(data)
        return cls.fernet.encrypt(payload.encode()).decode()

    @classmethod
    def decrypt(cls, token: str) -> dict:
        payload = cls.fernet.decrypt(token.encode()).decode()
        return json.loads(payload)
