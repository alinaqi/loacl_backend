from datetime import datetime
from typing import Optional

from pydantic import UUID4, BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base User model."""

    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""

    password: str


class UserUpdate(UserBase):
    """User update model."""

    password: Optional[str] = None


class UserInDB(UserBase):
    """User DB model."""

    id: UUID4
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserBase):
    """User response model."""

    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
