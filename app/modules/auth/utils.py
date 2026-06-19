import secrets
from fastapi import Request
from user_agents import parse

from app.modules.auth.sсhemas import SessionCacheData
from app.infrastructure.db.models import UserSession


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)

def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None


def parse_user_agent(request: Request) -> dict:
    ua_string = request.headers.get("user-agent", "")
    ua = parse(ua_string)

    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "other"

    return {
        "device_name": ua_string,
        "device_type": device_type,
        "browser": ua.browser.family,
        "os": ua.os.family,
        "ip_address": get_client_ip(request),
    }


def create_session_data(session_db: UserSession) -> SessionCacheData:
    return SessionCacheData(
        username=session_db.user.username,
        public_id=str(session_db.user.public_id),
        first_name=session_db.user.first_name,
        last_name=session_db.user.last_name,
        role=session_db.user.role,
    )