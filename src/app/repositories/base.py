"""
Base repository module for database operations.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from fastapi import Depends
from postgrest import APIResponse
from supabase import Client

from app.core.logger import get_logger
from app.core.supabase import get_supabase_client

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = get_logger(__name__)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository for database operations."""

    def __init__(self, client: Client = Depends(get_supabase_client)):
        """
        Initialize the repository.

        Args:
            client: Supabase client
        """
        self.client = client
        self.table_name = ""  # Override in child classes

    async def create(self, data: CreateSchemaType) -> APIResponse:
        """
        Create a new record.

        Args:
            data: Data to create

        Returns:
            APIResponse: Created record
        """
        try:
            return (
                await self.client.table(self.table_name)
                .insert(data.model_dump())
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to create {self.table_name}", error=str(e))
            raise

    async def get(self, id: UUID) -> Optional[Dict]:
        """
        Get record by ID.

        Args:
            id: Record ID

        Returns:
            Optional[Dict]: Record if found
        """
        try:
            response = (
                await self.client.table(self.table_name)
                .select("*")
                .eq("id", str(id))
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to get {self.table_name}", error=str(e))
            raise

    async def list(
        self, limit: int = 100, offset: int = 0, filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        List records with optional filtering.

        Args:
            limit: Maximum records to return
            offset: Number of records to skip
            filters: Optional filters

        Returns:
            List[Dict]: List of records
        """
        try:
            query = self.client.table(self.table_name).select("*")

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = await query.range(offset, offset + limit - 1).execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to list {self.table_name}", error=str(e))
            raise

    async def update(self, id: UUID, data: UpdateSchemaType) -> APIResponse:
        """
        Update a record.

        Args:
            id: Record ID
            data: Data to update

        Returns:
            APIResponse: Updated record
        """
        try:
            return (
                await self.client.table(self.table_name)
                .update(data.model_dump(exclude_unset=True))
                .eq("id", str(id))
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to update {self.table_name}", error=str(e))
            raise

    async def delete(self, id: UUID) -> APIResponse:
        """
        Delete a record.

        Args:
            id: Record ID

        Returns:
            APIResponse: Deletion response
        """
        try:
            return (
                await self.client.table(self.table_name)
                .delete()
                .eq("id", str(id))
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to delete {self.table_name}", error=str(e))
            raise
