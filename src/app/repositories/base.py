"""
Base repository module for database operations.
"""

from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel
from supabase.client import Client

from app.core.logger import get_logger

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

logger = get_logger(__name__)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository for database operations."""

    def __init__(self, client: Client):
        """
        Initialize the repository.

        Args:
            client: Supabase client
        """
        self._client = client
        self.table_name = ""  # Override in child classes

    async def create(self, data: CreateSchemaType) -> ModelType:
        """
        Create a new record.

        Args:
            data: Data to create

        Returns:
            ModelType: Created record
        """
        try:
            response = (
                await self._client.table(self.table_name)
                .insert(data.model_dump())
                .execute()
            )
            return ModelType(**response.data[0])
        except Exception as e:
            logger.error(
                f"Failed to create record in {self.table_name}", exc_info=str(e)
            )
            raise

    async def get(self, id: UUID) -> Optional[ModelType]:
        """
        Get record by ID.

        Args:
            id: Record ID

        Returns:
            Optional[ModelType]: Record if found
        """
        try:
            response = (
                await self._client.table(self.table_name)
                .select("*")
                .eq("id", str(id))
                .single()
                .execute()
            )
            return ModelType(**response.data) if response.data else None
        except Exception as e:
            logger.error(f"Failed to get {self.table_name}", error=str(e))
            raise

    async def list(
        self, filters: Optional[dict] = None, limit: int = 100, offset: int = 0
    ) -> List[ModelType]:
        """
        List records with optional filtering.

        Args:
            filters: Optional filters
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            List[ModelType]: List of records
        """
        try:
            query = self._client.table(self.table_name).select("*")

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = await query.range(offset, offset + limit - 1).execute()
            return [ModelType(**item) for item in response.data]
        except Exception as e:
            logger.error(f"Failed to list {self.table_name}", error=str(e))
            raise

    async def update(self, id: UUID, data: UpdateSchemaType) -> ModelType:
        """
        Update a record.

        Args:
            id: Record ID
            data: Data to update

        Returns:
            ModelType: Updated record
        """
        try:
            response = (
                await self._client.table(self.table_name)
                .update(data.model_dump(exclude_unset=True))
                .eq("id", str(id))
                .execute()
            )
            return ModelType(**response.data[0])
        except Exception as e:
            logger.error(f"Failed to update {self.table_name}", error=str(e))
            raise

    async def delete(self, id: UUID) -> None:
        """
        Delete a record.

        Args:
            id: Record ID
        """
        try:
            await self._client.table(self.table_name).delete().eq(
                "id", str(id)
            ).execute()
        except Exception as e:
            logger.error(f"Failed to delete {self.table_name}", error=str(e))
            raise
