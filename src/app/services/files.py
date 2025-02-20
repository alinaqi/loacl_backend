"""
File service module.
"""

import os
from datetime import datetime
from typing import BinaryIO, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import UploadFile
from supabase.client import Client

from app.core.logger import get_logger
from app.models.file import File, FileCreate, FileStatus
from app.repositories.file import FileRepository
from app.services.base import BaseService

logger = get_logger(__name__)


class FileService(BaseService):
    """Service for handling file storage operations."""

    def __init__(self, file_repository: FileRepository, supabase_client: Client):
        """
        Initialize the service.

        Args:
            file_repository: Repository for file operations
            supabase_client: Supabase client for storage operations
        """
        super().__init__()
        self.file_repository = file_repository
        self.storage_client = supabase_client.storage
        self.bucket_name = "files"  # Default bucket for file storage

    async def upload_file(
        self,
        file: UploadFile,
        thread_id: Optional[UUID] = None,
        message_id: Optional[UUID] = None,
        metadata: Optional[Dict] = None,
    ) -> File:
        """
        Upload a file to storage.

        Args:
            file: File to upload
            thread_id: Optional thread ID to associate with
            message_id: Optional message ID to associate with
            metadata: Optional metadata

        Returns:
            File: Created file record
        """
        try:
            # Generate a unique storage path
            file_id = uuid4()
            extension = os.path.splitext(file.filename)[1]
            storage_path = f"{file_id}{extension}"

            # Create file record
            file_data = FileCreate(
                filename=file.filename,
                content_type=file.content_type,
                size=0,  # Will be updated after upload
                metadata=metadata or {},
            )
            file_record = File(
                id=file_id, storage_path=storage_path, **file_data.model_dump()
            )

            # Upload to Supabase storage
            file_content = await file.read()
            await self.storage_client.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": file.content_type},
            )

            # Update file size
            file_record.size = len(file_content)
            file_record.status = FileStatus.READY

            # Create database record
            response = await self.file_repository.create(file_record)
            return File(**response.data[0])

        except Exception as e:
            logger.error("Failed to upload file", error=str(e))
            raise

    async def download_file(self, file_id: UUID) -> Optional[BinaryIO]:
        """
        Download a file from storage.

        Args:
            file_id: File ID

        Returns:
            Optional[BinaryIO]: File content if found
        """
        try:
            # Get file record
            file_data = await self.file_repository.get(file_id)
            if not file_data:
                return None

            file = File(**file_data)

            # Download from Supabase storage
            response = await self.storage_client.from_(self.bucket_name).download(
                file.storage_path
            )
            return response

        except Exception as e:
            logger.error("Failed to download file", error=str(e))
            raise

    async def delete_file(self, file_id: UUID) -> bool:
        """
        Delete a file from storage and database.

        Args:
            file_id: File ID

        Returns:
            bool: True if deleted successfully
        """
        try:
            # Get file record
            file_data = await self.file_repository.get(file_id)
            if not file_data:
                return False

            file = File(**file_data)

            # Delete from Supabase storage
            await self.storage_client.from_(self.bucket_name).remove(
                [file.storage_path]
            )

            # Delete database record
            await self.file_repository.delete(file_id)
            return True

        except Exception as e:
            logger.error("Failed to delete file", error=str(e))
            raise

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
            raise

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
            raise

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
            raise
