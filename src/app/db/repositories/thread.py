"""
Thread repository module.
"""

from typing import Optional
from uuid import UUID

from postgrest import APIResponse

from app.db.repositories.base import BaseRepository
from app.models.thread import Message, MessageCreate, Thread, ThreadCreate, ThreadUpdate


class ThreadRepository(BaseRepository[Thread, ThreadCreate, ThreadUpdate]):
    """Repository for thread operations."""

    def __init__(self) -> None:
        """Initialize the repository."""
        super().__init__("threads")

    async def get_with_messages(self, id: UUID) -> Optional[APIResponse]:
        """
        Get a thread with its messages.

        Args:
            id: Thread ID

        Returns:
            Optional[APIResponse]: Thread with messages or None
        """
        try:
            response = (
                await self.client.table(self.table_name)
                .select("*,messages(*)")
                .eq("id", str(id))
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            self.logger.error("Failed to get thread with messages", error=str(e))
            raise


class MessageRepository(BaseRepository[Message, MessageCreate, Message]):
    """Repository for message operations."""

    def __init__(self) -> None:
        """Initialize the repository."""
        super().__init__("messages")

    async def get_thread_messages(
        self,
        thread_id: UUID,
        limit: int = 100,
        offset: int = 0,
        ascending: bool = False,
    ) -> APIResponse:
        """
        Get messages for a thread.

        Args:
            thread_id: Thread ID
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            ascending: Sort in ascending order

        Returns:
            APIResponse: List of messages
        """
        try:
            query = (
                self.client.table(self.table_name)
                .select("*")
                .eq("thread_id", str(thread_id))
            )
            query = query.order("created_at", desc=not ascending)
            query = query.range(offset, offset + limit - 1)
            return await query.execute()
        except Exception as e:
            self.logger.error("Failed to get thread messages", error=str(e))
            raise
