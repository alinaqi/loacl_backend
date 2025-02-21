"""
Core configuration module for the LOACL application.
Handles all environment variables and application settings.
"""
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LOACL"
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # In production, replace with actual origins
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "txt", "doc", "docx"]
    UPLOAD_DIR: str = "uploads"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings() 