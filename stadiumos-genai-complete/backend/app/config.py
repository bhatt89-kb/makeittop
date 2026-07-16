"""
Central configuration for StadiumOS GenAI.

All values are read from environment variables to ensure no secrets are
hard-coded in source control. This module uses Pydantic Settings for automatic
validation, type checking, and .env file loading.

Design principles:
- All secrets (API keys, admin credentials) come from environment
- Sensible defaults for development, strict requirements for production
- Feature flags allow graceful degradation when services are unavailable
- LRU cache ensures single Settings instance across application

See `.env.example` for the complete list of supported environment variables.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        app_name: Human-readable application name for logging
        environment: Deployment environment (development/staging/production)
        debug: Enable debug mode with verbose logging
        gemini_api_key: Google Gemini API key for AI features
        gemini_model: Gemini model identifier (e.g., gemini-2.0-flash)
        ai_request_timeout_seconds: Maximum time to wait for AI responses
        ai_max_retries: Number of retry attempts for transient AI failures
        admin_api_key: Required credential for admin API endpoints
        allowed_origins: CORS-allowed origins for frontend connections
        rate_limit_requests: Maximum requests per time window per client
        rate_limit_window_seconds: Time window for rate limiting (seconds)
        max_request_body_bytes: Maximum allowed request body size
        redis_host: Redis server hostname for caching
        redis_port: Redis server port
        redis_db: Redis database number
        redis_enabled: Enable/disable Redis caching
        enable_rule_based_fallback: Keep app functional without AI key
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- Service identity -------------------------------------------------
    app_name: str = "StadiumOS GenAI"
    environment: str = Field(
        default="development",
        description="Deployment environment: development, staging, or production"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging"
    )

    # --- GenAI provider -----------------------------------------------------
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key. Empty string enables rule-based fallback mode."
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model identifier to use for generation"
    )
    ai_request_timeout_seconds: float = Field(
        default=20.0,
        gt=0,
        description="Maximum seconds to wait for AI API response"
    )
    ai_max_retries: int = Field(
        default=2,
        ge=0,
        description="Number of retry attempts for transient AI failures"
    )

    # --- Security -------------------------------------------------------
    admin_api_key: str = Field(
        default="",
        description="Required API key for admin endpoints. Empty disables admin access."
    )
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:8080"],
        description="CORS-allowed origins for API access"
    )
    rate_limit_requests: int = Field(
        default=30,
        gt=0,
        description="Maximum requests per time window per client IP"
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        gt=0,
        description="Time window for rate limiting (seconds)"
    )
    max_request_body_bytes: int = Field(
        default=20_000,
        gt=0,
        description="Maximum allowed request body size in bytes"
    )

    # --- Redis cache -------------------------------------------------------
    redis_host: str = Field(
        default="localhost",
        description="Redis server hostname"
    )
    redis_port: int = Field(
        default=6379,
        gt=0,
        description="Redis server port"
    )
    redis_db: int = Field(
        default=0,
        ge=0,
        description="Redis database number"
    )
    redis_enabled: bool = Field(
        default=True,
        description="Enable Redis caching. Disable for serverless or testing."
    )

    # --- Feature flags ----------------------------------------------------
    enable_rule_based_fallback: bool = Field(
        default=True,
        description="Keep app functional with rule-based logic when AI unavailable"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings singleton.
    
    Uses LRU cache to ensure settings are loaded once and reused across
    the application lifetime. This prevents repeated .env file reads.
    
    Returns:
        Settings instance loaded from environment variables
    """
    return Settings()
