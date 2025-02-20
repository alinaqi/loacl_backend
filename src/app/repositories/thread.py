"""
Thread repository module.
"""

from typing import List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class ThreadRepository(BaseRepository):
    """Repository for thread operations."""

    def __init__(self):
        """Initialize repository."""
        super().__init__()
        self.table_name = "lacl_threads"


class MessageRepository(BaseRepository):
    """Repository for message operations."""

    def __init__(self):
        """Initialize repository."""
        super().__init__()
        self.table_name = "lacl_messages"
