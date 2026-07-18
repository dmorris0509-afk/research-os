from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"), env_prefix="RESEARCH_OS_", extra="ignore"
    )

    environment: str = "development"
    database_url: str = "sqlite:///./research_os.db"
    workspace_root: Path = Path("workspace")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8501"])
    auth_required: bool = False
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"

    @field_validator("jwt_secret")
    @classmethod
    def validate_secret(cls, value: str | None) -> str | None:
        if value is not None and len(value) < 32:
            raise ValueError("JWT secret must contain at least 32 characters")
        return value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.auth_required and not settings.jwt_secret:
        raise ValueError("RESEARCH_OS_JWT_SECRET is required when authentication is enabled")
    return settings
