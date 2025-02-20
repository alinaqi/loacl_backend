"""
User preferences models module.
"""

from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import BaseModelTimestamps


class UserPreferencesBase(BaseModel):
    """Base user preferences model."""

    theme: str = Field(default="light", description="UI theme preference")
    language: str = Field(default="en", description="Language preference")
    timezone: str = Field(default="UTC", description="Timezone preference")
    notifications_enabled: bool = Field(
        default=True, description="Notifications enabled status"
    )
    preferences: Dict = Field(
        default_factory=dict, description="Additional preferences"
    )


class UserPreferencesCreate(UserPreferencesBase):
    """User preferences creation model."""

    user_id: UUID = Field(..., description="User ID")


class UserPreferencesUpdate(UserPreferencesBase):
    """User preferences update model."""

    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    preferences: Optional[Dict] = None


class UserPreferences(UserPreferencesBase, BaseModelTimestamps):
    """User preferences model with ID and timestamps."""

    id: UUID = Field(..., description="Unique identifier")
    user_id: UUID = Field(..., description="User ID")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "theme": "dark",
                "language": "en",
                "timezone": "America/New_York",
                "notifications_enabled": True,
                "preferences": {"font_size": "medium", "color_scheme": "blue"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }
