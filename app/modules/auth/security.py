import logging
import hashlib
import hmac
import secrets

from datetime import datetime, timedelta, timezone
from uuid import UUID

logger = logging.getLogger("teamboard")

from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import ValidationError

from app.modules.auth.sсhemas import AccessTokenPayload
from app.core.exceptions.exceptions import AppException, ErrorCode
from app.core.config import settings


class PasswordService:
    pwd_context = CryptContext(schemes=["argon2"],deprecated="auto")

    @classmethod
    def hash_password(cls, password: str) -> str:
        return cls.pwd_context.hash(password)

    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return cls.pwd_context.verify(password, hashed_password)


class TokenService:
    jwt_key = settings.security.jwt_secret
    refresh_key = settings.security.refresh_secret
    algorithm = settings.security.algorithm
    expire_minutes = settings.security.access_token_expire_min

    @classmethod
    def hash_refresh_token(cls, token: str) -> str:
        return hmac.new(cls.refresh_key.encode(), token.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def generate_refresh_token() -> str:
        return secrets.token_urlsafe(64)

    @classmethod
    def create_access_token(cls, public_id: UUID, session_id: UUID, role: str) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=cls.expire_minutes)

        payload_model = AccessTokenPayload(sub=public_id, sid=session_id, role=role, iat=now, exp=expire)

        return jwt.encode(claims=payload_model.model_dump(), key=cls.jwt_key, algorithm=cls.algorithm)

    @classmethod
    def decode_access_token(cls, token: str) -> AccessTokenPayload:
        try:
            payload = jwt.decode(token=token, key=cls.jwt_key, algorithms=[cls.algorithm])

            return AccessTokenPayload.model_validate(payload)

        except ExpiredSignatureError:
            logger.info(
                "Token expired",
                extra={"event": "auth_failed"}
            )
            raise AppException("Token expired",401, ErrorCode.TOKEN_EXPIRED)

        except (JWTError, ValidationError):
            logger.warning(
                "Invalid token",
                extra={"event": "auth_failed"}
            )

            raise AppException("Invalid token",401, ErrorCode.INVALID_TOKEN)

    @classmethod
    def hash_confirmation_code(cls, code: str) -> str:
        return hmac.new(cls.refresh_key.encode(), code.encode(), hashlib.sha256).hexdigest()