from typing import Optional

from app.models.assistant import Assistant
from app.repositories.base import BaseRepository


class AssistantRepository(BaseRepository):
    """Repository for assistant operations"""

    def __init__(self):
        super().__init__()
        self.table_name = "assistants"

    async def get_by_openai_id(self, openai_id: str) -> Optional[Assistant]:
        """
        Get assistant by OpenAI ID

        Args:
            openai_id: OpenAI assistant ID

        Returns:
            Optional[Assistant]: Assistant if found, None otherwise
        """
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE openai_assistant_id = :openai_id
            LIMIT 1
        """
        result = await self.db.fetch_one(query=query, values={"openai_id": openai_id})
        return Assistant(**result) if result else None
