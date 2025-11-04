"""Configuration management using Pydantic Settings."""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from life_organizer.schemas.enums import Category


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    api_version: str = Field(default="v1", description="API version")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # CORS Settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )

    # External Services (to be configured later)
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    claude_api_key: str = Field(..., description="Anthropic Claude API key")

    # Database (future)
    database_url: str | None = Field(default=None, description="Database connection URL")

    # iOS Integration (future)
    icloud_username: str | None = Field(default=None, description="iCloud username")
    icloud_password: str | None = Field(default=None, description="iCloud password")

    # File Storage (future)
    storage_path: str | None = Field(default=None, description="Path to file storage")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    # claude_api_key required, always set in .env
    return Settings()  # type: ignore[call-arg]


def _load_keyword_config() -> dict[Category, dict[str, float | dict[str, float]]]:
    """Load keyword configuration from JSON file.

    Returns:
        dict mapping Category to keyword configuration
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "keyword_config.json"
    with config_path.open() as f:
        data = json.load(f)

    return {
        Category.BUDGET: data["expense"],
        Category.SHOPPING: data["shopping"],
        Category.REMINDER: data["reminder"],
        Category.CALENDAR: data["calendar"],
    }


# Keyword-based classification configuration
KEYWORD_CONFIG = _load_keyword_config()
