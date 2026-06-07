from app.core.observability.logging_config import setup_logging
setup_logging()

from fastapi import FastAPI
from app.api.router import api_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.Exceptions.exceptions import AppException
from app.core.Exceptions.exeptions_handlers import app_exception_handler, general_exception_handler
from app.core.middleware.middleware import logging_middleware


STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="TeamBoard API") # app

# ---------------------- EXCEPTION HANDLERS ----------------------
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# ---------------------- MIDDLEWARE ----------------------
app.middleware("http")(logging_middleware)


# ---------------------- STATIC ----------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------- ROUTES ----------------------
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return FileResponse(STATIC_DIR  / "index.html")