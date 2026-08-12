from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Enterprise AI Assistant"
    google_api_key: str | None = Field(default=None, repr=False)
    gemini_model: str = "gemini-2.5-flash"
    database_url: str | None = None
    redis_url: str | None = None
    data_dir: Path = Path("data")
    max_upload_mb: int = 10
    log_level: str = "INFO"

    @property
    def vector_path(self) -> Path:
        return self.data_dir / "vectors.json"

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "assistant.db"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
