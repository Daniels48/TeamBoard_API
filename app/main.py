from app.core.logging_config import setup_logging
setup_logging()

from fastapi import FastAPI


app = FastAPI(title="TeamBoard API")

@app.get("/")
async def root():
    return {"message": "TeamBoard API is running 🚀"}
