from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import BaseModel

from app.core.observability.other_utils import get_git_version

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
    jwt_secret: str
    refresh_secret: str
    email_secret: str
    algorithm: str
    access_token_expire_min: int = 30
    refresh_token_expire_days: int = 7

    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_min * 60

    @property
    def refresh_token_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 60 * 60


class Settings(BaseSettings):
    db: DbSettings
    security: SecuritySettings
    logging: LoggingSettings

    version: str = get_git_version()

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