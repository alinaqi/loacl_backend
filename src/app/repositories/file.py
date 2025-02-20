"""
File repository module.
"""

from typing import Optional
from uuid import UUID

from app.core.logger import get_logger
from app.db.repositories.base import BaseRepository
from app.models.file import File, FileCreate, FileUpdate

logger = get_logger(__name__)


class FileRepository(BaseRepository[File, FileCreate, FileUpdate]):
    """Repository for file operations."""

    def __init__(self):
        """Initialize repository."""
        super().__init__("lacl_files")

    async def get_by_openai_id(self, openai_file_id: str) -> Optional[dict]:
        """
        Get a file by its OpenAI file ID.

        Args:
            openai_file_id: OpenAI file ID

        Returns:
            Optional[dict]: Found file or None
        """
        try:
            response = (
                await self.client.table(self.table_name)
                .select("*")
                .eq("openai_file_id", openai_file_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error("Failed to get file by OpenAI ID", error=str(e))
            raise

    async def get_thread_files(
        self,
        thread_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """
        Get files attached to a thread.

        Args:
            thread_id: Thread ID
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            dict: List of files
        """
        try:
            query = (
                self.client.table("thread_files")
                .select("files(*)")
                .eq("thread_id", str(thread_id))
            )
            query = query.range(offset, offset + limit - 1)
            return await query.execute()
        except Exception as e:
            logger.error("Failed to get thread files", error=str(e))
            raise

    async def attach_to_thread(self, file_id: UUID, thread_id: UUID) -> dict:
        """
        Attach a file to a thread.

        Args:
            file_id: File ID
            thread_id: Thread ID

        Returns:
            dict: Created attachment record
        """
        try:
            return (
                await self.client.table("thread_files")
                .insert(
                    {
                        "file_id": str(file_id),
                        "thread_id": str(thread_id),
                    }
                )
                .execute()
            )
        except Exception as e:
            logger.error("Failed to attach file to thread", error=str(e))
            raise

    async def detach_from_thread(self, file_id: UUID, thread_id: UUID) -> dict:
        """
        Detach a file from a thread.

        Args:
            file_id: File ID
            thread_id: Thread ID

        Returns:
            dict: Deleted attachment record
        """
        try:
            return (
                await self.client.table("thread_files")
                .delete()
                .match(
                    {
                        "file_id": str(file_id),
                        "thread_id": str(thread_id),
                    }
                )
                .execute()
            )
        except Exception as e:
            logger.error("Failed to detach file from thread", error=str(e))
            raise


def get_file_repository() -> FileRepository:
    """Get file repository instance."""
    return FileRepository()
