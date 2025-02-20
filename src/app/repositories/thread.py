"""
Thread repository module.
"""

from typing import List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.db.repositories.base import BaseRepository
from app.models.thread import Message, MessageCreate, Thread, ThreadCreate, ThreadUpdate

logger = get_logger(__name__)


class ThreadRepository(BaseRepository[Thread, ThreadCreate, ThreadUpdate]):
    """Repository for thread operations."""

    def __init__(self):
        """Initialize repository."""
        super().__init__("lacl_threads")


class MessageRepository(BaseRepository[Message, MessageCreate, Message]):
    """Repository for message operations."""

    def __init__(self):
        """Initialize repository."""
        super().__init__("lacl_messages")


def get_thread_repository() -> ThreadRepository:
    """Get thread repository instance."""
    return ThreadRepository()


def get_message_repository() -> MessageRepository:
    """Get message repository instance."""
    return MessageRepository()
