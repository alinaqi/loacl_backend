"""
Supabase client module.
"""

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings

settings = get_settings()


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get a cached Supabase client instance.

    Returns:
        Client: Supabase client instance
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_KEY,
    )
