"""Test health check endpoint."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_health_check(test_app: FastAPI, test_client: AsyncClient) -> None:
    """Test health check endpoint returns 200 and correct response."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
