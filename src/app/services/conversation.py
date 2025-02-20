"""
Conversation context management service.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import Depends

from app.core.logger import get_logger
from app.models.thread import Message, Thread
from app.repositories.thread import (
    MessageRepository,
    ThreadRepository,
    get_message_repository,
    get_thread_repository,
)
from app.services.base import BaseService

logger = get_logger(__name__)


class ConversationContextService(BaseService):
    """Service for managing conversation context."""

    def __init__(
        self,
        thread_repository: ThreadRepository = Depends(get_thread_repository),
        message_repository: MessageRepository = Depends(get_message_repository),
    ) -> None:
        """
        Initialize the service.

        Args:
            thread_repository: Repository for thread operations
            message_repository: Repository for message operations
        """
        super().__init__()
        self.thread_repository = thread_repository
        self.message_repository = message_repository
        self.context_window = 10  # Number of messages to include in context

    async def get_conversation_context(
        self,
        thread_id: UUID,
        message_id: Optional[UUID] = None,
        window_size: Optional[int] = None,
    ) -> List[Message]:
        """
        Get conversation context for a thread.

        Args:
            thread_id: Thread ID
            message_id: Optional message ID to get context around
            window_size: Optional custom window size

        Returns:
            List[Message]: List of context messages
        """
        try:
            # Use custom window size if provided
            context_size = window_size or self.context_window

            # Get messages before the current message
            response = await self.message_repository.get_thread_messages(
                thread_id=thread_id,
                limit=context_size,
                ascending=True,  # Get in chronological order
            )

            return [Message(**msg) for msg in response.data]

        except Exception as e:
            logger.error("Failed to get conversation context", error=str(e))
            raise

    async def summarize_context(
        self,
        thread_id: UUID,
        before_timestamp: Optional[datetime] = None,
    ) -> Optional[str]:
        """
        Summarize older context to save tokens.

        Args:
            thread_id: Thread ID
            before_timestamp: Summarize messages before this time

        Returns:
            Optional[str]: Context summary if available
        """
        try:
            # Get thread with messages
            thread = await self.thread_repository.get_with_messages(thread_id)
            if not thread:
                return None

            # Filter messages before timestamp if provided
            messages = [
                Message(**msg)
                for msg in thread.get("messages", [])
                if not before_timestamp or msg["created_at"] < before_timestamp
            ]

            if not messages:
                return None

            # Create a summary of the conversation
            summary = f"Previous conversation summary ({len(messages)} messages):\n"
            summary += "\n".join(
                f"- {msg.role}: {msg.content[:100]}..."
                for msg in messages[:5]  # Summarize first 5 messages
            )

            return summary

        except Exception as e:
            logger.error("Failed to summarize context", error=str(e))
            raise

    async def get_relevant_files(self, thread_id: UUID) -> List[str]:
        """
        Get relevant file IDs for context.

        Args:
            thread_id: Thread ID

        Returns:
            List[str]: List of relevant file IDs
        """
        try:
            thread = await self.thread_repository.get_with_messages(thread_id)
            if not thread:
                return []

            # Extract file IDs from message metadata
            file_ids = set()
            for message in thread.get("messages", []):
                files = message.get("metadata", {}).get("files", [])
                file_ids.update(files)

            return list(file_ids)

        except Exception as e:
            logger.error("Failed to get relevant files", error=str(e))
            raise
