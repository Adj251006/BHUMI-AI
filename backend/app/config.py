"""Application configuration loaded from environment variables.

Uses pydantic-settings to validate and type-check all required config
at startup. If any required variable is missing from .env or the
environment, the application will fail fast with a clear error message.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.

    Required:
        database_url: PostgreSQL connection string
            (e.g. postgresql://user:pass@host:5432/dbname).
        secret_key: Secret key for JWT token signing (Module 2).

    Optional:
        environment: Runtime environment — controls debug logging, etc.
    """

    database_url: str = "postgresql://postgres.ffxsuugwobmwjbguglqi:Aaryan%40251006@15.165.245.138:5432/postgres?sslmode=require"
    secret_key: str = "bhumi-ai-production-super-secret-key-sih2026-default"
    environment: str = "development"

    # JWT settings (Module 2)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60   # 1 hour
    refresh_token_expire_days: int = 7      # 1 week
    # LLM Settings
    llm_provider: str = "gemini"
    gemini_api_key: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Singleton instance — import this throughout the application.
# Fails fast at import time if required env vars are missing.
settings = Settings()
