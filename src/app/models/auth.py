"""
Authentication models module.
"""

from datetime import datetime
from typing import Optional
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

    device_id: Optional[str] = Field(None, description="Device identifier")
    metadata: Optional[dict] = Field(
        default_factory=dict, description="Session metadata"
    )


class GuestSessionResponse(BaseResponse):
    """Guest session response model."""

    session_id: UUID = Field(..., description="Session ID")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class SessionConversionRequest(BaseModel):
    """Request model for converting a guest session to an authenticated session."""

    session_id: UUID
    client_id: str
    client_secret: str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "client_id": "client_123",
                "client_secret": "secret_456",
            }
        }


class TokenRequest(BaseModel):
    """Token request model."""

    client_id: str = Field(..., description="Client ID for authentication")
    client_secret: str = Field(..., description="Client secret for authentication")


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_at": "2024-02-20T12:00:00Z",
            }
        }


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
