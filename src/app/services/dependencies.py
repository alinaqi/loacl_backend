"""
Core service dependencies.
"""

from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.supabase import get_supabase_client
from app.repositories.assistant import AssistantRepository
from app.repositories.thread import MessageRepository, ThreadRepository
from app.services.assistant import AssistantService
from app.services.auth import AuthService
from app.services.openai import OpenAIService
from app.services.thread import ThreadService


@lru_cache()
def get_openai_client() -> AsyncOpenAI:
    """Get cached OpenAI client instance."""
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@lru_cache()
def get_openai_service() -> OpenAIService:
    """Get cached OpenAI service instance."""
    client = get_openai_client()
    return OpenAIService(client)


@lru_cache()
def get_thread_service() -> ThreadService:
    """Get cached thread service instance."""
    client = get_supabase_client()
    thread_repo = ThreadRepository(client)
    openai_service = get_openai_service()
    return ThreadService(thread_repo, openai_service)


@lru_cache()
def get_assistant_service() -> AssistantService:
    """Get cached assistant service instance."""
    client = get_supabase_client()
    assistant_repo = AssistantRepository(client)
    openai_service = get_openai_service()
    return AssistantService(assistant_repo, openai_service)


@lru_cache()
def get_auth_service() -> AuthService:
    """Get cached auth service instance."""
    client = get_supabase_client()
    return AuthService(client)
