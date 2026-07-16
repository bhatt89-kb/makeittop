"""
Central configuration for StadiumOS GenAI.

All values are read from environment variables so that no secret is ever
hard-coded in source control. See `.env.example` for the full list of
variables the service understands.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Service identity -------------------------------------------------
    app_name: str = "StadiumOS GenAI"
    environment: str = Field(default="development")  # development | staging | production
    debug: bool = False

    # --- GenAI provider -----------------------------------------------------
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-2.0-flash")
    ai_request_timeout_seconds: float = 20.0
    ai_max_retries: int = 2

    # --- Security -------------------------------------------------------
    admin_api_key: str = Field(default="")  # required to hit /admin/* routes
    allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost:8080"])
    rate_limit_requests: int = 30          # requests
    rate_limit_window_seconds: int = 60    # per window, per client IP
    max_request_body_bytes: int = 20_000   # guards against oversized payloads

    # --- Redis cache -------------------------------------------------------
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    redis_enabled: bool = Field(default=True)

    # --- Feature flags ----------------------------------------------------
    enable_rule_based_fallback: bool = True  # keeps the app fully functional with no API key


@lru_cache
def get_settings() -> Settings:
    return Settings()
