from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.exceptions.exceptions import AppException
from app.core.exceptions.exeptions_handlers import app_exception_handler, general_exception_handler
from app.core.middleware.middleware import logging_middleware
from app.core.observability.logging_config import setup_logging
from app.web.router import router as pages_router

setup_logging()


app = FastAPI(title="TeamBoard API")  # app


# ---------------------- EXCEPTION HANDLERS ----------------------
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# ---------------------- MIDDLEWARE ----------------------
app.middleware("http")(logging_middleware)


# ---------------------- STATIC ----------------------
STATIC_DIR = Path(__file__).resolve().parent / "web" / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------- ROUTES ----------------------
app.include_router(pages_router)
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
