from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class UvicornSettings(BaseModel):
    host: str
    port: int
    reload: bool


class AuthSettings(BaseModel):
    login_expire_seconds: int
    jwt_private_key: str
    jwt_audience: str
    jwt_issuer: str


class CORSSettings(BaseModel):
    allow_origins: list[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]


class RewardsSettings(BaseModel):
    points_per_datapoint: int = 1
    points_per_level: int = 100


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='kruzinator__',
        env_nested_delimiter='__',
        extra="ignore",
        case_sensitive=False,
    )
    uvicorn: UvicornSettings
    auth: AuthSettings
    cors: CORSSettings = Field(default_factory=CORSSettings)
    rewards: RewardsSettings = Field(default_factory=RewardsSettings)

    environment: Literal["development", "production", "test"] = "development"
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    postgres_url: PostgresDsn
    exports_max_rows: int = 50_000



@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore
