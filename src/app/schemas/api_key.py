"""API key schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class APIKeyBase(BaseModel):
    """Base API key model."""

    name: str = Field(..., description="Name of the API key")


class APIKeyCreate(APIKeyBase):
    """API key creation model."""

    pass


class APIKeyUpdate(BaseModel):
    """API key update model."""

    name: Optional[str] = None
    is_active: Optional[bool] = None


class APIKeyInDB(APIKeyBase):
    """API key database model."""

    id: UUID
    user_id: UUID
    key: str
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class APIKeyResponse(APIKeyBase):
    """API key response model."""

    id: UUID
    created_at: datetime
    is_active: bool = True
    key: str

    class Config:
        from_attributes = True
