import hashlib, hmac, secrets
import logging
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError
from uuid import UUID

logger = logging.getLogger("teamboard")

from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError

from app.modules.auth.sсhemas import AccessTokenPayload
from app.core.exceptions.exceptions import AppException, ErrorCode
from app.core.config import settings


class PasswordService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["argon2"],deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(password, hashed_password)


class TokenService:
    def __init__(self):
        self.jwt_key = settings.security.jwt_secret
        self.refresh_key = settings.security.refresh_secret
        self.algorithm = settings.security.algorithm
        self.expire_minutes = settings.security.access_token_expire_min
        self.refresh_days = settings.security.refresh_token_expire_days


    def hash_refresh_token(self, token: str) -> str:
        return hmac.new(self.refresh_key.encode(), token.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def generate_refresh_token() -> str:
        return secrets.token_urlsafe(64)

    @staticmethod
    def generate_session_id() -> str:
        return secrets.token_urlsafe(32)

    def create_access_token(self, public_id: UUID, session_id: UUID, role: str) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.expire_minutes)

        payload_model = AccessTokenPayload(sub=public_id, sid=session_id, role=role, iat=now, exp=expire)

        return jwt.encode(claims=payload_model.model_dump(), key=self.jwt_key, algorithm=self.algorithm)


    def decode_access_token(self, token: str) -> AccessTokenPayload:
        try:
            payload = jwt.decode(
                token=token,
                key=self.jwt_key,
                algorithms=[self.algorithm],
            )
        except ExpiredSignatureError:
            raise AppException("Token expired", 401, ErrorCode.TOKEN_EXPIRED)
        except JWTError:
            logger.warning(
                "Invalid JWT",
                extra={"event": "auth_failed",}
            )

            raise AppException("Invalid token", 401, ErrorCode.INVALID_TOKEN)

        try:
            token_data = AccessTokenPayload(**payload)
        except ValidationError:
            logger.warning(
                "Invalid token payload",
                extra={"event": "auth_failed"}
            )
            raise AppException("Invalid token payload", 401, ErrorCode.INVALID_TOKEN)

        if token_data.type != "access":
            logger.warning(
                "Invalid token type",
                extra={"event": "auth_failed"}
            )
            raise AppException("Invalid token type", 401, ErrorCode.INVALID_TOKEN_TYPE)

        if not token_data.sub or not token_data.sid:
            logger.warning(
                "Invalid token payload",
                extra={"event": "auth_failed"}
            )
            raise AppException("Invalid token payload", 401, ErrorCode.INVALID_TOKEN)

        return token_data