"""
User preferences repository module.
"""

from typing import Optional
from uuid import UUID

from app.models.preferences import (
    UserPreferences,
    UserPreferencesCreate,
    UserPreferencesUpdate,
)
from app.repositories.base import BaseRepository


class UserPreferencesRepository(BaseRepository):
    """Repository for user preferences operations"""

    def __init__(self):
        super().__init__()
        self.table_name = "user_preferences"

    async def get_by_user_id(self, user_id: UUID) -> Optional[UserPreferences]:
        """
        Get user preferences by user ID.

        Args:
            user_id: User ID

        Returns:
            Optional[UserPreferences]: User preferences if found, None otherwise
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE user_id = :user_id
            LIMIT 1
        """
        result = await self.db.fetch_one(query=query, values={"user_id": user_id})
        return UserPreferences(**result) if result else None

    async def create_or_update(
        self, user_id: UUID, data: UserPreferencesCreate | UserPreferencesUpdate
    ) -> UserPreferences:
        """
        Create or update user preferences.

        Args:
            user_id: User ID
            data: User preferences data

        Returns:
            UserPreferences: Created or updated user preferences
        """
        # Check if preferences exist
        existing = await self.get_by_user_id(user_id)

        if existing:
            # Update existing preferences
            query = f"""
                UPDATE {self.table_name}
                SET theme = COALESCE(:theme, theme),
                    language = COALESCE(:language, language),
                    timezone = COALESCE(:timezone, timezone),
                    notifications_enabled = COALESCE(:notifications_enabled, notifications_enabled),
                    preferences = COALESCE(:preferences, preferences),
                    updated_at = NOW()
                WHERE user_id = :user_id
                RETURNING *
            """
        else:
            # Create new preferences
            query = f"""
                INSERT INTO {self.table_name} (
                    user_id, theme, language, timezone,
                    notifications_enabled, preferences
                )
                VALUES (
                    :user_id, :theme, :language, :timezone,
                    :notifications_enabled, :preferences
                )
                RETURNING *
            """

        values = {
            "user_id": user_id,
            "theme": data.theme,
            "language": data.language,
            "timezone": data.timezone,
            "notifications_enabled": data.notifications_enabled,
            "preferences": data.preferences,
        }

        result = await self.db.fetch_one(query=query, values=values)
        return UserPreferences(**result)
