"""
Dependency injection module.

This module provides a centralized dependency injection system for the application.
It uses FastAPI's dependency injection system combined with a custom container
for managing service dependencies.
"""

import uuid
from typing import AsyncGenerator, Callable, Dict, Optional, Type, TypeVar

from fastapi import Depends, Request
from openai import AsyncOpenAI
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from supabase import Client

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.core.supabase import get_supabase_client
from app.repositories.assistant import AssistantRepository
from app.repositories.base import BaseRepository
from app.repositories.thread import MessageRepository, ThreadRepository
from app.services.assistant import AssistantService
from app.services.conversation import ConversationContextService
from app.services.openai import OpenAIService

T = TypeVar("T")
logger = get_logger(__name__)


class DependencyContainer:
    """
    Dependency container for managing service instances.

    This container ensures that service instances are created only once
    and reused throughout the application lifecycle.
    """

    def __init__(self) -> None:
        """Initialize the dependency container."""
        self._instances: Dict[Type, object] = {}
        self._factories: Dict[Type, Callable] = {}
        self._settings: Optional[Settings] = None
        self._openai_client: Optional[AsyncOpenAI] = None
        self._supabase_client: Optional[Client] = None
        self._repositories: Dict[str, BaseRepository] = {}
        self._scoped_instances: Dict[str, Dict[Type, object]] = {}

    def get_settings(self) -> Settings:
        """Get application settings."""
        if not self._settings:
            self._settings = get_settings()
        return self._settings

    async def get_openai_client(self) -> AsyncOpenAI:
        """
        Get OpenAI client instance.

        Returns:
            AsyncOpenAI: OpenAI client instance
        """
        if not self._openai_client:
            settings = self.get_settings()
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

    async def get_openai_service(self) -> OpenAIService:
        """
        Get OpenAI service instance.

        Returns:
            OpenAIService: OpenAI service instance
        """
        if OpenAIService not in self._instances:
            client = await self.get_openai_client()
            self._instances[OpenAIService] = OpenAIService(client)
        return self._instances[OpenAIService]

    def get_supabase_client(self) -> Client:
        """
        Get Supabase client instance.

        Returns:
            Client: Supabase client instance
        """
        if not self._supabase_client:
            settings = self.get_settings()
            self._supabase_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY,
                options={"db_schema": "public"},
            )
        return self._supabase_client

    async def get_repository(self, repo_type: Type[BaseRepository]) -> BaseRepository:
        """
        Get a repository instance of the specified type.

        Args:
            repo_type: Type of repository to get

        Returns:
            BaseRepository: Repository instance
        """
        repo_name = repo_type.__name__
        if repo_name not in self._repositories:
            client = self.get_supabase_client()
            self._repositories[repo_name] = repo_type(client)
        return self._repositories[repo_name]

    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory function for creating service instances.

        Args:
            service_type: Type of service to register
            factory: Factory function to create service instances
        """
        self._factories[service_type] = factory

    async def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service instance of the specified type.

        Args:
            service_type: Type of service to get

        Returns:
            T: Service instance

        Raises:
            KeyError: If no factory is registered for the service type
        """
        if service_type not in self._instances:
            if service_type not in self._factories:
                raise KeyError(f"No factory registered for {service_type}")
            self._instances[service_type] = self._factories[service_type]()
        return self._instances[service_type]

    async def get_scoped_service(self, service_type: Type[T], scope_id: str) -> T:
        """
        Get a service instance scoped to a specific context (e.g., request).

        Args:
            service_type: Type of service to get
            scope_id: Identifier for the scope (e.g., request ID)

        Returns:
            T: Service instance

        Raises:
            KeyError: If no factory is registered for the service type
        """
        if scope_id not in self._scoped_instances:
            self._scoped_instances[scope_id] = {}

        if service_type not in self._scoped_instances[scope_id]:
            if service_type not in self._factories:
                raise KeyError(f"No factory registered for {service_type}")
            self._scoped_instances[scope_id][service_type] = self._factories[
                service_type
            ]()

        return self._scoped_instances[scope_id][service_type]

    def cleanup_scope(self, scope_id: str) -> None:
        """
        Clean up all services for a specific scope.

        Args:
            scope_id: Identifier for the scope to clean up
        """
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]

    async def get_assistant_service(self) -> AssistantService:
        """
        Get assistant service instance.

        Returns:
            AssistantService: Assistant service instance
        """
        if AssistantService not in self._instances:
            openai_service = await self.get_openai_service()
            assistant_repository = await self.get_repository(AssistantRepository)
            self._instances[AssistantService] = AssistantService(
                assistant_repository=assistant_repository,
                openai_service=openai_service,
            )
        return self._instances[AssistantService]

    async def get_conversation_context_service(self) -> ConversationContextService:
        """
        Get conversation context service instance.

        Returns:
            ConversationContextService: Conversation context service instance
        """
        if ConversationContextService not in self._instances:
            thread_repository = await self.get_repository(ThreadRepository)
            message_repository = await self.get_repository(MessageRepository)
            self._instances[ConversationContextService] = ConversationContextService(
                thread_repository=thread_repository,
                message_repository=message_repository,
            )
        return self._instances[ConversationContextService]


# Global container instance
container = DependencyContainer()


# FastAPI dependencies
async def get_di_container() -> DependencyContainer:
    """
    Get the dependency injection container.

    Returns:
        DependencyContainer: Global dependency container instance
    """
    return container


async def get_openai_service(
    container: DependencyContainer = Depends(get_di_container),
) -> AsyncGenerator[OpenAIService, None]:
    """
    FastAPI dependency for getting the OpenAI service.

    Args:
        container: Dependency container instance

    Yields:
        OpenAIService: OpenAI service instance
    """
    service = await container.get_openai_service()
    yield service


# Add FastAPI dependency for repository injection
async def get_repository_dependency(
    repo_type: Type[BaseRepository],
    container: DependencyContainer = Depends(get_di_container),
) -> AsyncGenerator[BaseRepository, None]:
    """
    FastAPI dependency for getting a repository instance.

    Args:
        repo_type: Type of repository to get
        container: Dependency container instance

    Yields:
        BaseRepository: Repository instance
    """
    repo = await container.get_repository(repo_type)
    yield repo


# Add FastAPI middleware for request scoping
class RequestScopeMiddleware(BaseHTTPMiddleware):
    """Middleware for request-scoped dependency injection."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        Process the request through middleware.

        Args:
            request: Current request
            call_next: Next middleware/endpoint

        Returns:
            Response: Response from next middleware/endpoint
        """
        try:
            # Initialize services
            settings = get_settings()
            supabase_client = get_supabase_client(settings)
            openai_service = OpenAIService(settings.OPENAI_API_KEY)

            # Initialize services
            assistant_service = AssistantService(
                settings=settings,
                client=supabase_client,
                openai_service=openai_service,
            )

            # Add to request state
            request.state.settings = settings
            request.state.supabase_client = supabase_client
            request.state.assistant_service = assistant_service

            return await call_next(request)
        except Exception as e:
            logger.error("Error in request scope middleware", exc_info=str(e))
            raise


# Add FastAPI dependency for scoped service injection
async def get_scoped_service_dependency(
    service_type: Type[T],
    request: Request,
    container: DependencyContainer = Depends(get_di_container),
) -> AsyncGenerator[T, None]:
    """
    FastAPI dependency for getting a request-scoped service instance.

    Args:
        service_type: Type of service to get
        request: Current request
        container: Dependency container instance

    Yields:
        T: Service instance
    """
    service = await container.get_scoped_service(service_type, request.state.scope_id)
    yield service


async def get_assistant_service(
    container: DependencyContainer = Depends(get_di_container),
) -> AsyncGenerator[AssistantService, None]:
    """
    FastAPI dependency for getting the assistant service.

    Args:
        container: Dependency container instance

    Yields:
        AssistantService: Assistant service instance
    """
    service = await container.get_assistant_service()
    yield service


async def get_conversation_context_service(
    container: DependencyContainer = Depends(get_di_container),
) -> AsyncGenerator[ConversationContextService, None]:
    """
    FastAPI dependency for getting the conversation context service.

    Args:
        container: Dependency container instance

    Yields:
        ConversationContextService: Conversation context service instance
    """
    service = await container.get_conversation_context_service()
    yield service
