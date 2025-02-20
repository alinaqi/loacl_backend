"""
Authentication models module.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.base import BaseResponse


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class LoginResponse(BaseResponse):
    """Login response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: UUID = Field(..., description="User ID")


class GuestSessionRequest(BaseModel):
    """Guest session request model."""

    metadata: Optional[Dict] = None


class GuestSessionResponse(BaseModel):
    """Guest session response model."""

    session_id: str
    expires_at: datetime


class SessionConversionRequest(BaseModel):
    """Session conversion request model."""

    session_id: str
    client_id: str


class TokenRequest(BaseModel):
    """Token request model."""

    client_id: str
    client_secret: str


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model for JWT claims."""

    user_id: UUID = Field(..., description="User ID from the token")
    exp: Optional[datetime] = Field(None, description="Token expiration timestamp")
    scope: Optional[str] = Field(None, description="Token scope")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "exp": "2024-02-20T12:00:00Z",
                "scope": "user",
            }
        }
