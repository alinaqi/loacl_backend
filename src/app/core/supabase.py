"""
Supabase client module.
"""

from functools import lru_cache

from fastapi import Depends
from supabase import Client, create_client

from app.core.config import Settings, get_settings


def create_supabase_client(url: str, key: str) -> Client:
    """
    Create a new Supabase client instance.

    Args:
        url: Supabase URL
        key: Supabase key

    Returns:
        Client: Supabase client instance
    """
    return create_client(url, key)


@lru_cache()
def get_cached_client(url: str, key: str) -> Client:
    """
    Get cached Supabase client instance.

    Args:
        url: Supabase URL
        key: Supabase key

    Returns:
        Client: Supabase client instance
    """
    return create_supabase_client(url, key)


def get_supabase_client(settings: Settings = Depends(get_settings)) -> Client:
    """
    Get Supabase client instance.

    Args:
        settings: Application settings

    Returns:
        Client: Supabase client instance
    """
    return get_cached_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
