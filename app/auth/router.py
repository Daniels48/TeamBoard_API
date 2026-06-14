import logging
from datetime import datetime, timezone

from fastapi import APIRouter, status, Depends, Request, Response, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.auth.cookies import set_refresh_cookie
from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.security import TokenService
from app.auth.service import AuthService, PasswordResetService
from app.auth.sсhemas import UserRegister, AccessTokenResponse, UserLogin, VerifyEmailRequest, ForgotPasswordRequest, \
    VerifyResetCodeRequest, ResetPasswordRequest
from app.core.Exceptions.exceptions import AppException
from app.core.redis_service import SessionCache
from app.db.database import get_db
from app.db.models import User
from app.db.repositories.session_repository import UserSessionRepository
from app.db.repositories.user_repository import UserRepository
from app.mail.service import EmailService

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

logger = logging.getLogger("teamboard")


def _build_auth_response(response: Response, tokens):
    set_refresh_cookie(response, tokens.get("refresh_token"))
    return {"access_token": tokens["access_token"]}


@auth_router.post(path="/register", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)):

    tokens = await auth_service.register(db, data, request)
    return _build_auth_response(response, tokens)


@auth_router.post(path="/login",response_model=AccessTokenResponse)
async def login(
    data: UserLogin,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)):

    tokens = await auth_service.login(db, data, request)
    return _build_auth_response(response, tokens)


@auth_router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)):

    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        logger.warning(
            "Refresh token in cookie is missing",
            extra={"event": "refresh_token_missing_cookie"},
        )
        raise AppException("Unauthorized", 401)

    return await auth_service.refresh(db, refresh_token)

@auth_router.delete("/sessions/{session_id}", status_code=200)
async def logout_device(
    session_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):

    session = await UserSessionRepository.get_by_session_id(db, session_id)

    if not session or session.user_id != current_user.id:
        raise AppException(status_code=404, message="Session not found")

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
async def logout_all(current_user=Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    await UserSessionRepository.revoke_all_session(db, current_user.id)
    return {"message": "Logged out"}

@auth_router.post("/send-verification-email")
async def send_verification_email(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)):

    if user.is_verified:
        raise AppException("Email already verified",400)

    token = await AuthService.generate_email_verification(db=db,user=user)

    background_tasks.add_task(EmailService.send_verification_email, user.email, token,)

    return {"message": "Verification email sent"}

@auth_router.post("/verify-email")
async def verify_email(data: VerifyEmailRequest,db: AsyncSession = Depends(get_db),user: User = Depends(get_current_user)):
    return await AuthService.verify_email(db=db, user=user, code=data.code)

@auth_router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)):

    user = await UserRepository.get_by_email(db=db, email=data.email)

    if user:
        code = await AuthService.generate_password_reset(db=db,user=user)
        background_tasks.add_task(EmailService.send_reset_password_email,user.email,code)

    else:
        raise AppException("Email not found")


    return {"message":"If the account exists, a reset code has been sent"}

@auth_router.post("/verify-reset-code")
async def verify_reset_code(
    data: VerifyResetCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await UserRepository.get_by_email(db=db,email=data.email,)

    if not user:
        raise AppException(
            "Invalid code",
            400,
        )

    if not user.password_reset_token_valid:
        raise AppException(
            "Code expired",
            400,
        )

    if user.password_reset_token != data.code:
        raise AppException(
            "Invalid code",
            400,
        )

    payload = {"email": user.email,"code": data.code}
    reset_token = PasswordResetService().encrypt(data=payload)

    return {"reset_token": reset_token}

@auth_router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)):

    await AuthService().reset_password(db=db, token=data.token, new_password=data.new_password)
    return {"message": "Password reset successfully"}
