"""
File service module.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile

from app.core.logger import get_logger
from app.models.file import File, FileCreate
from app.repositories.file import FileRepository, get_file_repository
from app.services.base import BaseService
from app.services.openai import OpenAIService

logger = get_logger(__name__)


class FileService(BaseService):
    """Service for handling file storage operations."""

    def __init__(
        self,
        file_repository: FileRepository = Depends(get_file_repository),
        openai_service: OpenAIService = Depends(),
    ) -> None:
        """
        Initialize the service.

        Args:
            file_repository: Repository for file operations
            openai_service: OpenAI service for API operations
        """
        super().__init__()
        self.file_repository = file_repository
        self.openai_service = openai_service

    async def upload_file(self, file: UploadFile) -> File:
        """
        Upload a file.

        Args:
            file: File to upload

        Returns:
            File: Uploaded file
        """
        try:
            # Upload to OpenAI
            openai_file = await self.openai_service.upload_file(file)

            # Create local file record
            file_data = FileCreate(
                name=file.filename,
                openai_file_id=openai_file.id,
                content_type=file.content_type,
                size=file.size,
            )
            response = await self.file_repository.create(file_data)
            return File(**response.data[0])

        except Exception as e:
            logger.error("Failed to upload file", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_file(self, file_id: UUID) -> Optional[File]:
        """
        Get a file by ID.

        Args:
            file_id: File ID

        Returns:
            Optional[File]: Found file or None
        """
        try:
            response = await self.file_repository.get(file_id)
            return File(**response) if response else None
        except Exception as e:
            logger.error("Failed to get file", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_file(self, file_id: UUID) -> None:
        """
        Delete a file.

        Args:
            file_id: File ID
        """
        try:
            # Get file first to check if it exists
            file = await self.get_file(file_id)
            if not file:
                raise HTTPException(status_code=404, detail="File not found")

            # Delete from OpenAI
            try:
                await self.openai_service.client.files.delete(file.openai_file_id)
            except Exception as e:
                logger.warning(f"Failed to delete OpenAI file: {str(e)}")

            # Delete local record
            await self.file_repository.delete(file_id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to delete file", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def get_thread_files(
        self,
        thread_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[File]:
        """
        Get files attached to a thread.

        Args:
            thread_id: Thread ID
            limit: Maximum number of files to return
            offset: Number of files to skip

        Returns:
            List[File]: List of files
        """
        try:
            response = await self.file_repository.get_thread_files(
                thread_id=thread_id,
                limit=limit,
                offset=offset,
            )
            return [File(**file_data) for file_data in response.data]

        except Exception as e:
            logger.error("Failed to get thread files", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def attach_to_thread(self, file_id: UUID, thread_id: UUID) -> None:
        """
        Attach a file to a thread.

        Args:
            file_id: File ID
            thread_id: Thread ID
        """
        try:
            await self.file_repository.attach_to_thread(file_id, thread_id)
        except Exception as e:
            logger.error("Failed to attach file to thread", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def detach_from_thread(self, file_id: UUID, thread_id: UUID) -> None:
        """
        Detach a file from a thread.

        Args:
            file_id: File ID
            thread_id: Thread ID
        """
        try:
            await self.file_repository.detach_from_thread(file_id, thread_id)
        except Exception as e:
            logger.error("Failed to detach file from thread", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
