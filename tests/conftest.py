"""Common test fixtures and configuration."""

import asyncio
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from postgrest import AsyncPostgrestClient

from app.core.config import get_settings
from app.main import app
from app.repositories.webhook import WebhookRepository
from app.services.analytics import AnalyticsService
from app.services.health import HealthService

settings = get_settings()

# Use a test schema in Supabase
TEST_SCHEMA = "test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def supabase() -> MagicMock:
    """Create a Supabase client for testing."""
    mock_client = MagicMock()
    mock_client.table.return_value = mock_client
    mock_client.select.return_value = mock_client
    mock_client.insert.return_value = mock_client
    mock_client.update.return_value = mock_client
    mock_client.delete.return_value = mock_client
    mock_client.eq.return_value = mock_client
    mock_client.execute.return_value = MagicMock(data=[])
    return mock_client


@pytest.fixture(scope="session")
def postgrest(supabase: MagicMock) -> AsyncPostgrestClient:
    """Get the Postgrest client for raw SQL execution."""
    return supabase.postgrest


@pytest.fixture(scope="session")
async def verify_schema(postgrest: AsyncPostgrestClient) -> None:
    """Verify that the test schema exists and has the required tables."""
    result = await postgrest.rpc("verify_test_schema").execute()
    assert (
        result.data is True
    ), "Test schema verification failed. Please ensure all required tables exist in the test schema."


@pytest.fixture(scope="session")
def test_app() -> FastAPI:
    """Create a test instance of the FastAPI application."""
    from app.main import create_application

    return create_application()


@pytest.fixture
def test_client(test_app: FastAPI) -> AsyncClient:
    """Create a test client for making HTTP requests."""
    return AsyncClient(app=test_app, base_url="http://test")


@pytest.fixture(autouse=True)
async def setup_test_schema(
    postgrest: AsyncPostgrestClient,
) -> AsyncGenerator[None, None]:
    """Set up a clean test schema before each test."""
    # Create test schema if it doesn't exist and switch to it
    await postgrest.rpc("create_test_schema").execute()

    yield

    # Clean up test data after test
    await postgrest.rpc("cleanup_test_schema").execute()


@pytest.fixture
def client() -> TestClient:
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: FastAPI test client
    """
    return TestClient(app)


@pytest.fixture
def mock_openai_service() -> AsyncMock:
    """
    Create a mock OpenAI service.

    Returns:
        AsyncMock: Mock OpenAI service
    """
    return AsyncMock()


@pytest.fixture
def mock_conversation_service() -> AsyncMock:
    """
    Create a mock conversation service.

    Returns:
        AsyncMock: Mock conversation service
    """
    return AsyncMock()


@pytest.fixture
def mock_webhook_repository() -> AsyncMock:
    """Create a mock webhook repository."""
    mock = AsyncMock(spec=WebhookRepository)
    return mock


@pytest.fixture
def mock_health_service() -> AsyncMock:
    """Create a mock health service."""
    mock = AsyncMock(spec=HealthService)
    return mock


@pytest.fixture
def mock_analytics_service() -> AsyncMock:
    """Create a mock analytics service."""
    mock = AsyncMock(spec=AnalyticsService)
    return mock
