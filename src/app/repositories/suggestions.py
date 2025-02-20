"""
Suggestions repository module.
"""

from typing import List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.models.suggestions import FollowUpSuggestion
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class SuggestionsRepository(BaseRepository):
    """Repository for suggestions operations."""

    def __init__(self):
        """Initialize repository."""
        super().__init__()
        self.table_name = "lacl_follow_up_suggestions"

    async def create(self, suggestion: FollowUpSuggestion) -> dict:
        """
        Create a new suggestion.

        Args:
            suggestion: Suggestion to create

        Returns:
            dict: Created suggestion data
        """
        try:
            response = await super().create(suggestion.model_dump())
            return response.data[0] if response.data else None

        except Exception as e:
            logger.error("Failed to create suggestion", error=str(e))
            raise

    async def get_thread_suggestions(
        self,
        thread_id: UUID,
        message_id: Optional[UUID] = None,
        limit: int = 3,
    ) -> List[dict]:
        """
        Get suggestions for a thread.

        Args:
            thread_id: Thread ID
            message_id: Optional message ID to filter by
            limit: Maximum number of suggestions to return

        Returns:
            List[dict]: List of suggestions
        """
        try:
            filters = {"thread_id": str(thread_id)}
            if message_id:
                filters["message_id"] = str(message_id)

            response = await self.list(
                filters=filters,
                limit=limit,
                order_by=["-created_at"],  # Get most recent suggestions
            )
            return response.data

        except Exception as e:
            logger.error("Failed to get thread suggestions", error=str(e))
            raise
