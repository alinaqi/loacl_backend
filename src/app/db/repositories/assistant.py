"""
Assistant repository module.
"""

from app.db.repositories.base import BaseRepository
from app.models.assistant import Assistant, AssistantCreate, AssistantUpdate


class AssistantRepository(BaseRepository[Assistant, AssistantCreate, AssistantUpdate]):
    """Repository for assistant operations."""

    def __init__(self) -> None:
        """Initialize the repository."""
        super().__init__("assistants")
