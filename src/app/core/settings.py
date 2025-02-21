from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LOACL"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Security Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_API_MODEL: str = "gpt-4-turbo-preview"

    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "txt", "doc", "docx"]
    UPLOAD_DIR: str = "uploads"

    model_config = ConfigDict(case_sensitive=True, env_file=".env")

settings = Settings() 