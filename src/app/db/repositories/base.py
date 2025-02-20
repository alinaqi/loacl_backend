"""
Base repository module.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from postgrest import APIResponse
from supabase.client import Client

from app.core.logging import get_logger
from app.db.client import get_supabase_client

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = get_logger(__name__)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository for Supabase operations."""

    def __init__(self, table_name: str) -> None:
        """
        Initialize the repository.

        Args:
            table_name: Name of the table in Supabase
        """
        self.client: Client = get_supabase_client()
        self.table_name = table_name

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

    async def get(self, id: UUID) -> Optional[APIResponse]:
        """
        Get a record by ID.

        Args:
            id: Record ID

        Returns:
            Optional[APIResponse]: Found record or None
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
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        ascending: bool = False,
    ) -> APIResponse:
        """
        List records with optional filtering and pagination.

        Args:
            filters: Optional filters to apply
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Column to order by
            ascending: Sort in ascending order

        Returns:
            APIResponse: List of records
        """
        try:
            query = self.client.table(self.table_name).select("*")

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            if order_by:
                query = query.order(order_by, desc=not ascending)

            query = query.range(offset, offset + limit - 1)

            return await query.execute()
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
            APIResponse: Deleted record
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
