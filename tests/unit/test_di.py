"""
Test dependency injection system.
"""

from uuid import uuid4

import pytest
from openai import AsyncOpenAI

from app.core.di import DependencyContainer
from app.repositories.base import BaseRepository
from app.services.openai import OpenAIService


@pytest.fixture
def container() -> DependencyContainer:
    """Create a test dependency container."""
    return DependencyContainer()


@pytest.mark.asyncio
async def test_get_openai_service(container: DependencyContainer, monkeypatch) -> None:
    """Test getting OpenAI service from container."""
    # Mock settings to avoid loading from environment
    monkeypatch.setattr(
        container,
        "get_settings",
        lambda: type("Settings", (), {"OPENAI_API_KEY": "test-key"})(),
    )

    # Get service instance
    service = await container.get_openai_service()

    # Verify it's the correct type
    assert isinstance(service, OpenAIService)

    # Verify client is properly injected
    assert isinstance(service.client, AsyncOpenAI)

    # Verify singleton behavior
    service2 = await container.get_openai_service()
    assert service is service2  # Same instance


@pytest.mark.asyncio
async def test_register_factory(container: DependencyContainer) -> None:
    """Test registering and using a factory."""

    class TestService:
        def __init__(self) -> None:
            self.value = "test"

    # Register factory
    container.register_factory(TestService, TestService)

    # Get service instance
    service = await container.get_service(TestService)

    # Verify it's the correct type
    assert isinstance(service, TestService)
    assert service.value == "test"

    # Verify singleton behavior
    service2 = await container.get_service(TestService)
    assert service is service2  # Same instance


@pytest.mark.asyncio
async def test_get_unregistered_service(container: DependencyContainer) -> None:
    """Test getting an unregistered service raises error."""

    class UnregisteredService:
        pass

    # Attempt to get unregistered service
    with pytest.raises(KeyError):
        await container.get_service(UnregisteredService)


@pytest.mark.asyncio
async def test_get_repository(container: DependencyContainer, monkeypatch) -> None:
    """Test getting repository from container."""

    class TestRepository(BaseRepository):
        def __init__(self, client) -> None:
            super().__init__("test_table")

    # Mock supabase client
    monkeypatch.setattr(
        container,
        "get_supabase_client",
        lambda: type("Client", (), {})(),
    )

    # Get repository instance
    repo = await container.get_repository(TestRepository)

    # Verify it's the correct type
    assert isinstance(repo, TestRepository)

    # Verify singleton behavior
    repo2 = await container.get_repository(TestRepository)
    assert repo is repo2  # Same instance


@pytest.mark.asyncio
async def test_scoped_service(container: DependencyContainer) -> None:
    """Test scoped service management."""

    class TestService:
        def __init__(self) -> None:
            self.value = "test"

    # Register factory
    container.register_factory(TestService, TestService)

    # Create two different scopes
    scope1 = str(uuid4())
    scope2 = str(uuid4())

    # Get service in first scope
    service1 = await container.get_scoped_service(TestService, scope1)
    assert isinstance(service1, TestService)

    # Get same service in first scope - should be same instance
    service1_again = await container.get_scoped_service(TestService, scope1)
    assert service1 is service1_again

    # Get service in second scope - should be different instance
    service2 = await container.get_scoped_service(TestService, scope2)
    assert isinstance(service2, TestService)
    assert service1 is not service2

    # Clean up first scope
    container.cleanup_scope(scope1)

    # Get service in first scope again - should be new instance
    service1_new = await container.get_scoped_service(TestService, scope1)
    assert isinstance(service1_new, TestService)
    assert service1 is not service1_new
