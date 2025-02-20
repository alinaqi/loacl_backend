"""
Thread service module.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException

from app.core.logger import get_logger
from app.models.thread import Thread, ThreadCreate, ThreadUpdate
from app.repositories.thread import ThreadRepository
from app.services.base import BaseService
from app.services.openai import OpenAIService

logger = get_logger(__name__)


class ThreadService(BaseService):
    """Service for managing threads."""

    def __init__(
        self,
        thread_repository: ThreadRepository,
        openai_service: OpenAIService,
    ) -> None:
        """
        Initialize the service.

        Args:
            thread_repository: Repository for thread operations
            openai_service: OpenAI service for API operations
        """
        super().__init__()
        self.thread_repository = thread_repository
        self.openai_service = openai_service

    async def create_thread(self, data: ThreadCreate) -> Thread:
        """
        Create a new thread.

        Args:
            data: Thread creation data

        Returns:
            Thread: Created thread
        """
        try:
            # Create OpenAI thread first
            openai_thread = await self.openai_service.create_thread(
                metadata={"assistant_id": str(data.assistant_id)}
            )

            # Create local thread record
            thread_data = Thread(
                id=UUID(int=0),  # Will be replaced by database
                assistant_id=data.assistant_id,
                openai_thread_id=openai_thread.id,
                title=data.title,
                metadata=data.metadata,
            )
            response = await self.thread_repository.create(thread_data)
            return Thread(**response.data[0])

        except Exception as e:
            logger.error("Failed to create thread", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_thread(self, thread_id: UUID) -> Optional[Thread]:
        """
        Get a thread by ID.

        Args:
            thread_id: Thread ID

        Returns:
            Optional[Thread]: Found thread or None
        """
        try:
            response = await self.thread_repository.get(thread_id)
            return Thread(**response) if response else None
        except Exception as e:
            logger.error("Failed to get thread", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_thread(self, thread_id: UUID) -> None:
        """
        Delete a thread.

        Args:
            thread_id: Thread ID
        """
        try:
            # Get thread first to check if it exists
            thread = await self.get_thread(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")

            # Delete from OpenAI
            try:
                await self.openai_service.client.beta.threads.delete(
                    thread.openai_thread_id
                )
            except Exception as e:
                logger.warning(f"Failed to delete OpenAI thread: {str(e)}")

            # Delete local record
            await self.thread_repository.delete(thread_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to delete thread", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_guest_threads(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> List[Thread]:
        """
        Get threads for a guest session.

        Args:
            session_id: Guest session ID
            limit: Maximum number of threads to return
            offset: Number of threads to skip

        Returns:
            List[Thread]: List of threads
        """
        try:
            response = await self.thread_repository.list(
                filters={"metadata->session_id": session_id},
                limit=limit,
                offset=offset,
            )
            return [Thread(**thread) for thread in response.data]
        except Exception as e:
            logger.error("Failed to get guest threads", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
