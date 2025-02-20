"""
User models module.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.base import BaseModelTimestamps


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr = Field(..., description="User's email address")
    is_active: bool = Field(default=True, description="Whether the user is active")
    is_superuser: bool = Field(
        default=False, description="Whether the user is a superuser"
    )
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., description="User's password")


class UserUpdate(UserBase):
    """User update model."""

    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    metadata: Optional[Dict] = None


class User(UserBase, BaseModelTimestamps):
    """User model with ID and timestamps."""

    id: UUID = Field(..., description="Unique identifier")


class UserResponse(BaseModel):
    """User response model."""

    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User's email address")
    is_active: bool = Field(..., description="Whether the user is active")
    is_superuser: bool = Field(..., description="Whether the user is a superuser")


class UserInDB(User):
    """User model with hashed password for database storage."""

    hashed_password: str = Field(..., description="Hashed password")


class Token(BaseModel):
    """Token model for authentication."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
