from enum import Enum


class ErrorCode(str, Enum):
    # base
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    # auth
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN_TYPE = "INVALID_TOKEN_TYPE"

    # session
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_REVOKED = "SESSION_REVOKED"

    # user
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_NOT_ACTIVE = "USER_NOT_ACTIVE"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    USERNAME_TAKEN = "USERNAME_TAKEN"

    # optional
    PERMISSION_DENIED = "PERMISSION_DENIED"
    BAD_REQUEST = "BAD_REQUEST"
    CONFLICT = "CONFLICT"


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: ErrorCode = ErrorCode.VALIDATION_ERROR,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code

    def __str__(self):
        return self.message


class NotFoundException(AppException):
    def __init__(self, message: str = "Not found"):
        super().__init__(
            message=message,
            status_code=404,
            code=ErrorCode.NOT_FOUND,
        )
