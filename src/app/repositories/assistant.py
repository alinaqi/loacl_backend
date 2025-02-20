"""
Assistant repository module.
"""

from typing import Optional
from uuid import UUID

from supabase.client import Client

from app.models.assistant import Assistant, AssistantCreate, AssistantUpdate
from app.repositories.base import BaseRepository


class AssistantRepository(BaseRepository[Assistant, AssistantCreate, AssistantUpdate]):
    """Repository for assistant operations."""

    def __init__(self, client: Client):
        """Initialize repository with client."""
        super().__init__(client)
        self.table_name = "assistants"

    async def get_by_openai_id(self, openai_id: str) -> Optional[Assistant]:
        """
        Get assistant by OpenAI ID.

        Args:
            openai_id: OpenAI assistant ID

        Returns:
            Optional[Assistant]: Assistant if found
        """
        response = (
            await self._client.table(self.table_name)
            .select("*")
            .eq("openai_assistant_id", openai_id)
            .single()
            .execute()
        )
        return Assistant(**response.data) if response.data else None

    async def get_current(self) -> Optional[Assistant]:
        """
        Get current assistant configuration.

        Returns:
            Optional[Assistant]: Current assistant if found
        """
        response = (
            await self._client.table(self.table_name)
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return Assistant(**response.data[0]) if response.data else None
