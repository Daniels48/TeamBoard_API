import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.exceptions import AppException, ErrorCode

logger = logging.getLogger("teamboard")


async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(
        str(exc),
        extra={
            "event": "app_error",
            "status_code": exc.status_code,
            "error_code": exc.code,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc),
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception",
        extra={
            "event": "internal_error",
            "status_code": 500,
            "error_code": ErrorCode.INTERNAL_ERROR,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": ErrorCode.INTERNAL_ERROR,
        },
    )
