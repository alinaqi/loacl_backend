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
    full_name: str = Field(..., description="User's full name")
    is_active: bool = Field(default=True, description="Whether the user is active")
    metadata: Dict = Field(default_factory=dict, description="Additional user metadata")


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8, description="User's password")


class UserUpdate(BaseModel):
    """User update model."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = None


class User(UserBase, BaseModelTimestamps):
    """Complete user model with ID and timestamps."""

    id: UUID = Field(..., description="Unique identifier")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class UserInDB(User):
    """User model with hashed password for database storage."""

    hashed_password: str = Field(..., description="Hashed password")


class Token(BaseModel):
    """Token model for authentication."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
