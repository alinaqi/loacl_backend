"""Common test fixtures and configuration."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from postgrest import AsyncPostgrestClient
from supabase import Client, create_client

from src.app.core.config import get_settings
from src.app.main import app

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
def supabase() -> Client:
    """Create a Supabase client for testing."""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_KEY,
    )


@pytest.fixture(scope="session")
def postgrest(supabase: Client) -> AsyncPostgrestClient:
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
async def test_app(verify_schema: None) -> FastAPI:
    """Create a test instance of the FastAPI application."""
    return app


@pytest.fixture(scope="session")
async def test_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for making HTTP requests."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


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
