# ============================================================
# config.py — DeciDr
# Centralized secure configuration using pydantic-settings
# All secrets loaded from .env — NEVER hardcoded here
# ============================================================

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    """
    All app configuration loaded securely from environment variables.
    Pydantic validates types and raises clear errors if required
    vars are missing — app will NOT start with broken config.
    """

    # --- App ---
    app_name: str = "DeciDr"
    app_version: str = "0.1.0"
    app_env: Literal["development", "production"] = Field(default="development")
    app_secret_key: str = Field(min_length=16)

    # --- Groq AI API ---
    groq_api_key: str = Field(
        description="Groq API key — get free at console.groq.com"
    )
    groq_model: str = Field(
        default="openai/gpt-oss-120b",
        description="Groq model ID. See console.groq.com/docs/deprecations"
    )
    # --- Tavily Web Search ---
    tavily_api_key: str = Field(
        default="",description="Tavily API key for web search — get free at tavily.com"
    )

    # --- CORS ---
    allowed_origin: str = Field(default="http://localhost:3000")

    # --- Rate Limiting ---
    rate_limit_per_minute: int = Field(default=10, ge=1, le=100)

    # --- Database ---
    database_url: str = Field(default="sqlite+aiosqlite:///./decidr.db")

    # --- Logging ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    @field_validator("app_secret_key")
    @classmethod
    def secret_key_must_not_be_placeholder(cls, v: str) -> str:
        """Prevent running with a placeholder secret key"""
        dangerous = ["your_secret", "changeme", "secret", "password", "generate_a_random"]
        if any(d in v.lower() for d in dangerous):
            raise ValueError(
                "APP_SECRET_KEY looks like a placeholder. "
                "Generate a real random key at randomkeygen.com"
            )
        return v

    @field_validator("groq_api_key")
    @classmethod
    def api_key_must_not_be_placeholder(cls, v: str) -> str:
        """Prevent running with a placeholder API key"""
        if v == "your_groq_api_key_here" or len(v) < 10:
            raise ValueError(
                "GROQ_API_KEY is a placeholder. "
                "Get a real free key at console.groq.com"
            )
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings — .env is read exactly once at startup,
    not on every request. Efficient and secure.
    Usage: settings = get_settings()
    """
    return Settings()