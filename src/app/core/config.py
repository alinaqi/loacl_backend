"""
Application configuration module.
"""

import logging
from functools import lru_cache
from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Project Info
    PROJECT_NAME: str = "LOACL Backend"
    PROJECT_DESCRIPTION: str = "Local OpenAI Assistant API Backend"
    VERSION: str = "0.1.0"

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]  # Add your frontend URL

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # OpenAI Configuration
    OPENAI_API_KEY: str

    # Environment Configuration
    ENV: str = "development"
    DEBUG: bool = True

    # Logging Configuration
    LOG_LEVEL: Union[str, int] = logging.INFO
    LOG_FORMAT: str = "json"  # Options: json, text
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_ROTATION_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_ROTATION_COUNT: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields in the settings
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
