"""
Supabase client module.
"""

from functools import lru_cache

from fastapi import Depends
from supabase import Client, create_client

from app.core.config import Settings, get_settings


@lru_cache()
def get_supabase_client(settings: Settings = Depends(get_settings)) -> Client:
    """
    Get cached Supabase client instance.

    Args:
        settings: Application settings

    Returns:
        Client: Supabase client instance
    """
    return create_client(
        settings.SUPABASE_URL, settings.SUPABASE_KEY, options={"db_schema": "public"}
    )
