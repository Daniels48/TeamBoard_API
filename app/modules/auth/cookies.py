from app.core.config import settings

path_refresh_token = "/api/auth"


def set_refresh_cookie(response, refresh_token: str):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # True в production (https)
        samesite="lax",
        max_age=settings.security.refresh_token_expire_seconds,
        path=path_refresh_token,
    )


def delete_refresh_cookie(response):
    response.delete_cookie(key="refresh_token", path=path_refresh_token)
