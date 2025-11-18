"""
Configuration management for Int Crucible.

Loads configuration from environment variables and provides validated settings
for all Crucible components, including Kosmos integration.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class CrucibleConfig(BaseSettings):
    """Int Crucible configuration."""

    # Database configuration (shared with Kosmos)
    database_url: str = Field(
        default="sqlite:///crucible.db",
        description="Database URL (shared with Kosmos)",
        alias="DATABASE_URL"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        alias="LOG_LEVEL"
    )
    
    # API configuration
    api_host: str = Field(
        default="127.0.0.1",
        description="API server host",
        alias="API_HOST"
    )
    
    api_port: int = Field(
        default=8000,
        description="API server port",
        alias="API_PORT"
    )
    
    # Kosmos configuration passthrough
    # These will be read by Kosmos's config system
    # LLM_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.
    # are handled by Kosmos directly

    model_config = SettingsConfigDict(
        populate_by_name=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra fields for Kosmos configuration
    )


# Global config instance
_config: Optional[CrucibleConfig] = None


def get_config() -> CrucibleConfig:
    """Get the global Crucible configuration."""
    global _config
    if _config is None:
        _config = CrucibleConfig()
    return _config

