from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """User registration request model."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login request model."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload model."""

    email: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""

    id: str
    email: EmailStr
    is_active: bool = True
