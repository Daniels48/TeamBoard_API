from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import BaseModel

from app.core.versions import get_git_version

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class LoggingSettings(BaseModel):
    log_level: str = "INFO"


class DbSettings(BaseModel):
    name: str
    host: str
    user: str
    port: int
    password: str


class SecuritySettings(BaseModel):
    secret_key: str
    algorithm: str
    access_token_expire_min: int = 30


class Settings(BaseSettings):
    db: DbSettings
    security: SecuritySettings
    logging: LoggingSettings

    version: str = get_git_version()  # 👈 добавляем сюда

    model_config = {
        "env_file": BASE_DIR / ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": "__"
    }

    @property
    def async_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db.user}:"
            f"{self.db.password}@{self.db.host}:"
            f"{self.db.port}/{self.db.name}"
        )

    @property
    def sync_db_url(self) -> str:
        return (
            f"postgresql://{self.db.user}:"
            f"{self.db.password}@{self.db.host}:"
            f"{self.db.port}/{self.db.name}"
        )


settings = Settings()