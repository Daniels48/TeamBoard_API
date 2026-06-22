from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

STATIC_DIR = Path(__file__).resolve().parent / "static"


@router.get("/boards/{board_id}")
async def board_page(board_id: str):
    return FileResponse(STATIC_DIR / "board.html")


@router.get("/boards")
async def boards_page():
    return FileResponse(STATIC_DIR / "boards.html")


@router.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/login")
async def login_page():
    return FileResponse(STATIC_DIR / "login.html")


@router.get("/register")
async def register_page():
    return FileResponse(STATIC_DIR / "register.html")


@router.get("/profile")
async def profile_page():
    return FileResponse(STATIC_DIR / "profile.html")


@router.get("/reset-password")
async def reset_password_page():
    return FileResponse(STATIC_DIR / "reset-password.html")


@router.get("/forgot-password")
async def forgot_password_page():
    return FileResponse(STATIC_DIR / "forgot-password.html")
