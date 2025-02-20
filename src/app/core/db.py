"""
Database connection module.
"""

from typing import AsyncGenerator

from databases import Database
from fastapi import Depends

from app.core.config import Settings, get_settings


async def get_database(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[Database, None]:
    """
    Get database connection.

    Args:
        settings: Application settings

    Returns:
        Database: Database connection
    """
    database = Database(settings.DATABASE_URL)
    if not database.is_connected:
        await database.connect()
    try:
        yield database
    finally:
        if database.is_connected:
            await database.disconnect()
