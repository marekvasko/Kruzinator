from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "info"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/kruzinator",
        validation_alias="DATABASE_URL",
    )

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])

    exports_max_rows: int = 50_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
