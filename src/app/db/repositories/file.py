"""
File repository module.
"""
from typing import Optional
from uuid import UUID

from postgrest import APIResponse

from app.db.repositories.base import BaseRepository
from app.models.file import File, FileCreate, FileUpdate


class FileRepository(BaseRepository[File, FileCreate, FileUpdate]):
    """Repository for file operations."""
    
    def __init__(self) -> None:
        """Initialize the repository."""
        super().__init__("files")
    
    async def get_by_openai_id(self, openai_file_id: str) -> Optional[APIResponse]:
        """
        Get a file by its OpenAI file ID.
        
        Args:
            openai_file_id: OpenAI file ID
        
        Returns:
            Optional[APIResponse]: Found file or None
        """
        try:
            response = await self.client.table(self.table_name).select("*").eq(
                "openai_file_id", openai_file_id
            ).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            self.logger.error("Failed to get file by OpenAI ID", error=str(e))
            raise
    
    async def get_thread_files(
        self,
        thread_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> APIResponse:
        """
        Get files attached to a thread.
        
        Args:
            thread_id: Thread ID
            limit: Maximum number of files to return
            offset: Number of files to skip
        
        Returns:
            APIResponse: List of files
        """
        try:
            query = self.client.table("thread_files").select(
                "files(*)"
            ).eq("thread_id", str(thread_id))
            query = query.range(offset, offset + limit - 1)
            return await query.execute()
        except Exception as e:
            self.logger.error("Failed to get thread files", error=str(e))
            raise
    
    async def attach_to_thread(self, file_id: UUID, thread_id: UUID) -> APIResponse:
        """
        Attach a file to a thread.
        
        Args:
            file_id: File ID
            thread_id: Thread ID
        
        Returns:
            APIResponse: Created attachment record
        """
        try:
            return await self.client.table("thread_files").insert({
                "file_id": str(file_id),
                "thread_id": str(thread_id),
            }).execute()
        except Exception as e:
            self.logger.error("Failed to attach file to thread", error=str(e))
            raise
    
    async def detach_from_thread(self, file_id: UUID, thread_id: UUID) -> APIResponse:
        """
        Detach a file from a thread.
        
        Args:
            file_id: File ID
            thread_id: Thread ID
        
        Returns:
            APIResponse: Deleted attachment record
        """
        try:
            return await self.client.table("thread_files").delete().match({
                "file_id": str(file_id),
                "thread_id": str(thread_id),
            }).execute()
        except Exception as e:
            self.logger.error("Failed to detach file from thread", error=str(e))
            raise 