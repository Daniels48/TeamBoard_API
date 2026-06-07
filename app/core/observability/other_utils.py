from fastapi import Request
from user_agents import parse
import subprocess


SENSITIVE_QUERY = {"token", "password", "secret"}


def get_protocol(request: Request) -> str:
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        return forwarded_proto

    return request.url.scheme


def sanitize_query(params: dict):
    return {
        k: "***" if k in SENSITIVE_QUERY else v
        for k, v in params.items()
    }


def parse_user_agent(user_agent: str | None):

    if not user_agent:
        return {}

    ua = parse(user_agent)

    if ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    else:
        device_type = "desktop"

    return {
        "user_agent_origin": user_agent,
        "browser": ua.browser.family,
        "browser_version": ua.browser.version_string,
        "os": ua.os.family,
        "os_version": ua.os.version_string or None,
        "device": ua.device.family,
        "device_type": device_type,
    }


def get_git_version() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        # Заглушка если git недоступен
        return "0.0.0-dev"
