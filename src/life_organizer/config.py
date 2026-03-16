"""Configuration management using Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Authentication
    api_key: str = Field(..., description="API key for authenticating client requests")

    # External Services (to be configured later)
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    claude_api_key: str = Field(..., description="Anthropic Claude API key")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://life_organizer:life_organizer@localhost:5432/life_organizer",
        description="Database connection URL (async format)",
    )

    @property
    def async_database_url(self) -> str:
        """Convert DATABASE_URL to async format if needed.

        Railway and some other platforms provide DATABASE_URL with postgresql://
        prefix, but asyncpg requires postgresql+asyncpg://. This property handles
        the conversion automatically.

        Returns:
            str: Database URL in async format (postgresql+asyncpg://)
        """
        if self.database_url and self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url or ""

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
