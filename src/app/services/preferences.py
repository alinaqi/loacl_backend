"""
User preferences service module.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.models.preferences import (
    UserPreferences,
    UserPreferencesCreate,
    UserPreferencesUpdate,
)
from app.repositories.preferences import UserPreferencesRepository
from app.services.base import BaseService

logger = get_logger(__name__)


class UserPreferencesService(BaseService):
    """Service for managing user preferences."""

    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        preferences_repo: UserPreferencesRepository = Depends(),
    ):
        """
        Initialize the service.

        Args:
            settings: Application settings
            preferences_repo: Repository for user preferences operations
        """
        super().__init__()
        self.settings = settings
        self.preferences_repo = preferences_repo

    async def get_preferences(self, user_id: UUID) -> UserPreferences:
        """
        Get user preferences.

        Args:
            user_id: User ID

        Returns:
            UserPreferences: User preferences
        """
        try:
            # Get preferences from repository
            preferences = await self.preferences_repo.get_by_user_id(user_id)

            # If no preferences exist, create default ones
            if not preferences:
                default_prefs = UserPreferencesCreate(user_id=user_id)
                preferences = await self.preferences_repo.create_or_update(
                    user_id=user_id, data=default_prefs
                )

            return preferences
        except Exception as e:
            logger.error("Failed to get user preferences", error=str(e))
            raise

    async def update_preferences(
        self, user_id: UUID, data: UserPreferencesUpdate
    ) -> UserPreferences:
        """
        Update user preferences.

        Args:
            user_id: User ID
            data: Update data

        Returns:
            UserPreferences: Updated user preferences
        """
        try:
            # Update preferences in repository
            return await self.preferences_repo.create_or_update(
                user_id=user_id, data=data
            )
        except Exception as e:
            logger.error("Failed to update user preferences", error=str(e))
            raise
