"""
Base repository module for database operations.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from databases import Database
from fastapi import Depends
from postgrest import APIResponse
from supabase import Client

from app.core.db import get_database
from app.core.logging import get_logger

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = get_logger(__name__)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository for database operations."""

    def __init__(self, db: Database = Depends(get_database)):
        """
        Initialize the repository.

        Args:
            db: Database connection
        """
        self.db = db
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

    async def get(self, id: Any) -> Optional[Dict]:
        """
        Get record by ID.

        Args:
            id: Record ID

        Returns:
            Optional[Dict]: Record if found
        """
        query = f"SELECT * FROM {self.table_name} WHERE id = :id"
        return await self.db.fetch_one(query=query, values={"id": id})

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
        query = f"SELECT * FROM {self.table_name}"
        if filters:
            conditions = " AND ".join(f"{k} = :{k}" for k in filters.keys())
            query += f" WHERE {conditions}"
        query += " LIMIT :limit OFFSET :offset"

        values = {**(filters or {}), "limit": limit, "offset": offset}

        return await self.db.fetch_all(query=query, values=values)

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
