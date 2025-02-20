"""
Authentication models module.
"""

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
    """Session conversion request model."""

    session_id: UUID = Field(..., description="Guest session ID to convert")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")
    full_name: str = Field(..., description="User's full name")
