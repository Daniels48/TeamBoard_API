import logging

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, status, Request, Response, BackgroundTasks

from app.modules.auth.session_repository import UserSessionRepository
from app.modules.auth.utils import parse_user_agent
from app.modules.users.user_repository import UserRepository
from app.modules.auth.cookies import set_refresh_cookie, delete_refresh_cookie
from app.modules.auth.service import AuthService, PasswordResetService
from app.modules.auth.sсhemas import (UserRegister, AccessTokenResponse, UserLogin, VerifyEmailRequest,
                                      ForgotPasswordRequest, VerifyResetCodeRequest, ResetPasswordRequest,
                                      UserSessionResponse)
from app.core.exceptions.exceptions import AppException
from app.core.dependencies import DBSession, CurrentUser
from app.infrastructure.redis.service import SessionCache
from app.infrastructure.mail.service import EmailService


auth_router = APIRouter(prefix="/auth", tags=["Auth"])

logger = logging.getLogger("teamboard")


def set_auth_cookies_and_build_response(response: Response, tokens):
    set_refresh_cookie(response, tokens.get("refresh_token"))
    return {"access_token": tokens["access_token"]}

@auth_router.post(path="/register", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, response: Response, request: Request, db: DBSession):
    device_info = parse_user_agent(request)
    tokens = await AuthService.register(db, data, device_info)
    return set_auth_cookies_and_build_response(response, tokens)

@auth_router.post(path="/login",response_model=AccessTokenResponse)
async def login(data: UserLogin,response: Response, request: Request,db: DBSession):
    device_info = parse_user_agent(request)
    tokens = await AuthService.login(db, data, device_info)
    return set_auth_cookies_and_build_response(response, tokens)

@auth_router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(request: Request,db: DBSession):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        logger.warning(
            "Refresh token in cookie is missing",
            extra={"event": "refresh_token_missing_cookie"},
        )
        raise AppException("Unauthorized", 401)

    return await AuthService.refresh(db, refresh_token)

@auth_router.get("/sessions",response_model=list[UserSessionResponse],)
async def get_active_sessions(current_user: CurrentUser, db: DBSession):
    sessions = await UserSessionRepository.get_active_by_user_id(db=db,user_id=current_user.id)
    return sessions

@auth_router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, db: DBSession) -> None:
    refresh_token = request.cookies.get("refresh_token")
    await AuthService.logout_current_session(db=db,refresh_token=refresh_token)
    delete_refresh_cookie(response)

@auth_router.delete("/sessions/{session_id}", status_code=204)
async def logout_device(session_id: UUID, current_user: CurrentUser, db: DBSession):
    await AuthService.logout_session(db=db,session_id=session_id, user_id=current_user.id)

@auth_router.post("/logout-all", status_code=204)
async def logout_all_sessions(current_user: CurrentUser, db: DBSession):
    await AuthService.logout_all_sessions(db=db,user_id=current_user.id)

@auth_router.post("/send-verification-email")
async def send_verification_email(background_tasks: BackgroundTasks, db: DBSession, user: CurrentUser):
    code = await AuthService.create_email_verification_code(db=db,user=user)
    background_tasks.add_task(EmailService.send_verification_email, user.email, code)

@auth_router.post("/verify-email")
async def verify_email(data: VerifyEmailRequest, user: CurrentUser, db: DBSession):
    return await AuthService.verify_email(db=db, user=user, code=data.code)

@auth_router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: DBSession):

    user = await UserRepository.get_by_email(db=db, email=data.email)

    if not user:
        raise AppException("If the account exists, a reset code has been sent")

    code = await AuthService.create_password_reset_code(db=db,user=user)
    background_tasks.add_task(EmailService.send_reset_password_email,user.email,code)

    return {"message":"If the account exists, a reset code has been sent"}

@auth_router.post("/verify-reset-code")
async def verify_reset_code(data: VerifyResetCodeRequest,db: DBSession):
    user = await AuthService.verify_reset_code(db=db, email=data.email, code=data.code)

    payload = {"email": user.email,"code": data.code}
    reset_token = PasswordResetService.encrypt(data=payload)

    return {"reset_token": reset_token}

@auth_router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest,db: DBSession):
    await AuthService.reset_password(db=db, token=data.token, new_password=data.new_password)
    return {"message": "Password reset successfully"}
