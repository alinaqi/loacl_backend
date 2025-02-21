"""
Core configuration module for the LOACL application.
Handles all environment variables and application settings.
"""

from functools import lru_cache
from typing import List, Union

from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings
from supabase.lib.client_options import ClientOptions

from supabase import Client, create_client


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LOACL"

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = ["*"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenAI
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_API_MODEL: str = "gpt-4-turbo-preview"

    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES: str = "pdf,txt,doc,docx"
    UPLOAD_DIR: str = "uploads"

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert ALLOWED_FILE_TYPES string to list."""
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    print(f"Loaded OpenAI API key: {settings.OPENAI_API_KEY[:10]}...")  # Debug print
    return settings


@lru_cache()
def get_supabase_client() -> Client:
    settings = get_settings()
    # Use service role key for admin access
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
