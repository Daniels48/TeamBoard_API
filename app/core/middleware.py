import time
import uuid
import logging
from fastapi import Request
from starlette.responses import Response

logger = logging.getLogger("teamboard")


def generate_request_id(incoming_id: str | None) -> str:
    return incoming_id or str(uuid.uuid4())



async def logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()

    request_id = generate_request_id(
        request.headers.get("X-Request-ID")
    )

    request.state.request_id = request_id

    try:
        response: Response = await call_next(request)
        status_code = response.status_code

    except Exception:
        duration = (time.perf_counter() - start_time) * 1000

        logger.exception(
            "Unhandled exception",
            extra={
                "service": "teamboard-api",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration, 2),
            },
        )
        raise

    duration = (time.perf_counter() - start_time) * 1000

    if status_code >= 500:
        level = logging.ERROR
    elif status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO

    logger.log(
        level,
        "HTTP request processed",
        extra={
            "service": "teamboard-api",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": round(duration, 2),
        },
    )

    response.headers["X-Request-ID"] = request_id

    return response

