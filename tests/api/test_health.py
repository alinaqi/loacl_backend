"""
Tests for health check endpoints.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from app.models.health import ServiceHealth, ServiceStatus


@pytest.fixture
def mock_health_service():
    """Create a mock health service."""
    return AsyncMock()


async def test_get_health(
    app: FastAPI,
    client: AsyncClient,
    mock_health_service: AsyncMock,
):
    """Test getting basic health status."""
    # Setup
    mock_health = ServiceHealth(
        status=ServiceStatus.HEALTHY,
        version="1.0.0",
        uptime=123.45,
    )
    mock_health_service.get_basic_health.return_value = mock_health

    # Execute
    response = await client.get("/health")

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == ServiceStatus.HEALTHY
    assert data["version"] == "1.0.0"
    assert data["uptime"] == 123.45
    mock_health_service.get_basic_health.assert_called_once()


async def test_get_detailed_health(
    app: FastAPI,
    client: AsyncClient,
    mock_health_service: AsyncMock,
):
    """Test getting detailed health status."""
    # Setup
    mock_health = {
        "status": ServiceStatus.HEALTHY,
        "version": "1.0.0",
        "uptime": 123.45,
        "database_latency": 5.67,
        "memory_usage": 256.0,
        "cpu_usage": 25.5,
        "open_connections": 10,
        "active_requests": 5,
        "dependencies": {"database": ServiceStatus.HEALTHY},
        "metrics": {"thread_count": 4, "open_files": 8},
    }
    mock_health_service.get_detailed_health.return_value = mock_health

    # Execute
    response = await client.get("/health/detailed")

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == ServiceStatus.HEALTHY
    assert data["version"] == "1.0.0"
    assert data["uptime"] == 123.45
    assert data["database_latency"] == 5.67
    assert data["memory_usage"] == 256.0
    assert data["cpu_usage"] == 25.5
    assert data["open_connections"] == 10
    assert data["active_requests"] == 5
    assert data["dependencies"]["database"] == ServiceStatus.HEALTHY
    assert data["metrics"]["thread_count"] == 4
    assert data["metrics"]["open_files"] == 8
    mock_health_service.get_detailed_health.assert_called_once()
