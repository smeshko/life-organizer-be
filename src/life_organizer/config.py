"""Configuration management using Pydantic Settings."""

from functools import lru_cache

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


# Keyword-based classification configuration
KEYWORD_CONFIG: dict[Category, dict[str, float | dict[str, float]]] = {
    Category.EXPENSE: {
        "keywords": {
            # High confidence expense indicators
            "spent": 1.0,
            "paid": 1.0,
            "cost": 0.9,
            "purchased": 0.9,
            "bought": 0.9,
            "charge": 0.8,
            "charged": 0.8,
            # Income keywords
            "received": 1.0,
            "got": 0.9,
            "earned": 0.9,
            "salary": 0.9,
            "rent": 0.8,
            "income": 0.8,
            # Savings keywords
            "saved": 1.0,
            "invested": 0.9,
            "saving": 0.8,
            "deposit": 0.8,
            # Currency indicators
            "eur": 0.7,
            "euro": 0.7,
            "euros": 0.7,
            "usd": 0.7,
            "dollar": 0.7,
            "dollars": 0.7,
            "$": 0.7,
            "€": 0.7,
            "bgn": 0.7,
            "lev": 0.7,
            "leva": 0.7,
            # Merchant/context keywords
            "restaurant": 0.6,
            "cafe": 0.6,
            "coffee": 0.5,
            "gas": 0.5,
            "grocery": 0.6,
            "groceries": 0.6,
            "supermarket": 0.6,
            "amazon": 0.5,
        }
    },
    Category.SHOPPING: {
        "keywords": {
            # High confidence shopping indicators
            "need": 0.9,
            "need to buy": 1.0,
            "buy": 0.8,
            "out of": 1.0,
            "running low": 0.9,
            "add to list": 1.0,
            "add to the list": 1.0,
            "shopping list": 1.0,
            "grocery list": 1.0,
            # Common items
            "milk": 0.7,
            "bread": 0.7,
            "eggs": 0.7,
            "coffee": 0.6,
            "grocery": 0.7,
            "groceries": 0.7,
        }
    },
    Category.REMINDER: {
        "keywords": {
            # High confidence reminder indicators
            "remind": 1.0,
            "reminder": 1.0,
            "don't forget": 1.0,
            "remember to": 0.9,
            "need to": 0.7,
            # Actions that typically need reminders
            "call": 0.8,
            "pick up": 0.8,
            "take out": 0.7,
            "trash": 0.6,
            "refill": 0.7,
            "send": 0.6,
            "email": 0.5,
        }
    },
    Category.CALENDAR: {
        "keywords": {
            # High confidence calendar indicators
            "meeting": 1.0,
            "appointment": 1.0,
            "schedule": 0.9,
            "scheduled": 0.9,
            "event": 0.8,
            "calendar": 1.0,
            # Time-based indicators
            "at": 0.5,  # "meeting at 2pm"
            "on": 0.5,  # "appointment on monday"
            "tomorrow": 0.6,
            "next week": 0.6,
            "tonight": 0.6,
        }
    },
}
