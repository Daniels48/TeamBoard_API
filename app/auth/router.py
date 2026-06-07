import logging
from datetime import datetime, timezone

from fastapi import APIRouter, status, Depends, Request, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.auth.cookies import set_refresh_cookie
from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.security import TokenService
from app.auth.service import AuthService
from app.auth.sсhemas import UserRegister, AccessTokenResponse, UserLogin
from app.core.Exceptions.exceptions import AppException
from app.core.redis_service import SessionCache
from app.db.database import get_db
from app.db.repositories.session_repository import UserSessionRepository

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

logger = logging.getLogger("teamboard")


def _build_auth_response(response: Response, tokens):
    set_refresh_cookie(response, tokens.get("refresh_token"))
    return {"access_token": tokens["access_token"]}


@auth_router.post(path="/register",response_model=AccessTokenResponse,status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.register(db, data, request)
    return _build_auth_response(response, tokens)


@auth_router.post(path="/login",response_model=AccessTokenResponse)
async def login(
    data: UserLogin,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = await auth_service.login(db, data, request)
    return _build_auth_response(response, tokens)


@auth_router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        logger.warning(
            "Refresh token in cookie is missing",
            extra={"event": "refresh_token_missing_cookie"},
        )
        raise AppException("Unauthorized", 401)

    access_token = await auth_service.refresh(db, refresh_token)

    return {"access_token": access_token}


@auth_router.delete("/sessions/{session_id}", status_code=204)
async def logout_device(
    session_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    session = await UserSessionRepository.get_by_session_id(db, session_id)

    if not session or session.user_id != current_user.id:
        raise HTTPException(404, "Session not found")

    session.revoked_at = datetime.now(timezone.utc)

    await SessionCache.delete(str(session_id))

    await db.commit()

    return {"message": "Logged out"}

@auth_router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        refresh_hash = TokenService().hash_refresh_token(refresh_token)

        session = await UserSessionRepository.get_by_refresh_hash(db, refresh_hash)

        if session:
            await SessionCache.delete(str(session.session_id))
            session.revoked_at = datetime.now(timezone.utc)

    response.delete_cookie("refresh_token")

    return {"message": "Logged out"}


@auth_router.post("/logout-all", status_code=204)
async def logout_all(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await UserSessionRepository.revoke_all(db, current_user.id)

    return {"message": "Logged out"}