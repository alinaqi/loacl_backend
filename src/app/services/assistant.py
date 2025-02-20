"""
Assistant service module.
"""

from typing import Dict, List, Optional
from uuid import UUID

from openai.types.beta import Assistant as OpenAIAssistant

from app.core.logger import get_logger
from app.models.assistant import Assistant, AssistantCreate, AssistantUpdate
from app.repositories.assistant import AssistantRepository
from app.services.base import BaseService
from app.services.openai import OpenAIService

logger = get_logger(__name__)


class AssistantService(BaseService):
    """Service for managing assistants."""

    def __init__(
        self,
        assistant_repository: AssistantRepository,
        openai_service: OpenAIService,
    ) -> None:
        """
        Initialize the service.

        Args:
            assistant_repository: Repository for assistant operations
            openai_service: OpenAI service for API operations
        """
        super().__init__()
        self.assistant_repository = assistant_repository
        self.openai_service = openai_service

    async def create_assistant(
        self,
        data: AssistantCreate,
    ) -> Assistant:
        """
        Create a new assistant.

        Args:
            data: Assistant creation data

        Returns:
            Assistant: Created assistant
        """
        try:
            # Create OpenAI assistant first
            openai_assistant = await self.openai_service.create_assistant(
                name=data.name,
                instructions=data.instructions,
                model=data.model,
                tools=data.tools,
                metadata=data.metadata,
            )

            # Create local assistant record
            assistant_data = Assistant(
                id=UUID(int=0),  # Will be replaced by database
                openai_assistant_id=openai_assistant.id,
                **data.model_dump(),
            )
            response = await self.assistant_repository.create(assistant_data)
            return Assistant(**response.data[0])

        except Exception as e:
            logger.error("Failed to create assistant", error=str(e))
            raise

    async def get_assistant(self, assistant_id: UUID) -> Optional[Assistant]:
        """
        Get an assistant by ID.

        Args:
            assistant_id: Assistant ID

        Returns:
            Optional[Assistant]: Found assistant or None
        """
        try:
            response = await self.assistant_repository.get(assistant_id)
            return Assistant(**response) if response else None
        except Exception as e:
            logger.error("Failed to get assistant", error=str(e))
            raise

    async def list_assistants(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict] = None,
    ) -> List[Assistant]:
        """
        List assistants with optional filtering.

        Args:
            limit: Maximum number of assistants to return
            offset: Number of assistants to skip
            filters: Optional filters to apply

        Returns:
            List[Assistant]: List of assistants
        """
        try:
            response = await self.assistant_repository.list(
                limit=limit,
                offset=offset,
                filters=filters,
            )
            return [Assistant(**data) for data in response.data]
        except Exception as e:
            logger.error("Failed to list assistants", error=str(e))
            raise

    async def update_assistant(
        self,
        assistant_id: UUID,
        data: AssistantUpdate,
    ) -> Assistant:
        """
        Update an assistant.

        Args:
            assistant_id: Assistant ID
            data: Update data

        Returns:
            Assistant: Updated assistant
        """
        try:
            # Get current assistant
            current = await self.get_assistant(assistant_id)
            if not current:
                raise ValueError(f"Assistant {assistant_id} not found")

            # Update OpenAI assistant
            await self.openai_service.client.beta.assistants.update(
                assistant_id=current.openai_assistant_id,
                name=data.name or current.name,
                instructions=data.instructions or current.instructions,
                model=data.model or current.model,
                tools=data.tools or current.tools,
                metadata=data.metadata or current.metadata,
            )

            # Update local record
            response = await self.assistant_repository.update(assistant_id, data)
            return Assistant(**response.data[0])

        except Exception as e:
            logger.error("Failed to update assistant", error=str(e))
            raise

    async def delete_assistant(self, assistant_id: UUID) -> bool:
        """
        Delete an assistant.

        Args:
            assistant_id: Assistant ID

        Returns:
            bool: True if deleted successfully
        """
        try:
            # Get current assistant
            current = await self.get_assistant(assistant_id)
            if not current:
                return False

            # Delete OpenAI assistant
            await self.openai_service.client.beta.assistants.delete(
                assistant_id=current.openai_assistant_id,
            )

            # Delete local record
            await self.assistant_repository.delete(assistant_id)
            return True

        except Exception as e:
            logger.error("Failed to delete assistant", error=str(e))
            raise

    async def add_file_to_assistant(
        self,
        assistant_id: UUID,
        file_id: str,
    ) -> Assistant:
        """
        Add a file to an assistant.

        Args:
            assistant_id: Assistant ID
            file_id: OpenAI file ID

        Returns:
            Assistant: Updated assistant
        """
        try:
            # Get current assistant
            current = await self.get_assistant(assistant_id)
            if not current:
                raise ValueError(f"Assistant {assistant_id} not found")

            # Add file to OpenAI assistant
            await self.openai_service.client.beta.assistants.files.create(
                assistant_id=current.openai_assistant_id,
                file_id=file_id,
            )

            # Update local record with file ID
            files = current.metadata.get("files", [])
            files.append(file_id)
            data = AssistantUpdate(metadata={"files": files})
            response = await self.assistant_repository.update(assistant_id, data)
            return Assistant(**response.data[0])

        except Exception as e:
            logger.error("Failed to add file to assistant", error=str(e))
            raise

    async def remove_file_from_assistant(
        self,
        assistant_id: UUID,
        file_id: str,
    ) -> Assistant:
        """
        Remove a file from an assistant.

        Args:
            assistant_id: Assistant ID
            file_id: OpenAI file ID

        Returns:
            Assistant: Updated assistant
        """
        try:
            # Get current assistant
            current = await self.get_assistant(assistant_id)
            if not current:
                raise ValueError(f"Assistant {assistant_id} not found")

            # Remove file from OpenAI assistant
            await self.openai_service.client.beta.assistants.files.delete(
                assistant_id=current.openai_assistant_id,
                file_id=file_id,
            )

            # Update local record
            files = current.metadata.get("files", [])
            if file_id in files:
                files.remove(file_id)
                data = AssistantUpdate(metadata={"files": files})
                response = await self.assistant_repository.update(assistant_id, data)
                return Assistant(**response.data[0])
            return current

        except Exception as e:
            logger.error("Failed to remove file from assistant", error=str(e))
            raise
