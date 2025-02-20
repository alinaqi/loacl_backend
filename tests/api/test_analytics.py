"""
Tests for analytics endpoints.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from app.models.analytics import TimeSeriesMetric, UsageMetrics, UsageStatistics


@pytest.fixture
def mock_analytics_service():
    """Create a mock analytics service."""
    return AsyncMock()


@pytest.fixture
def usage_statistics():
    """Create sample usage statistics."""
    now = datetime.utcnow()
    start_date = now - timedelta(days=7)

    return UsageStatistics(
        start_date=start_date,
        end_date=now,
        metrics=UsageMetrics(
            total_requests=1000,
            total_threads=50,
            total_messages=200,
            total_tokens=50000,
            total_files=25,
            average_response_time=150.5,
        ),
        requests_over_time=[
            TimeSeriesMetric(timestamp=start_date + timedelta(days=i), value=100.0)
            for i in range(7)
        ],
        tokens_over_time=[
            TimeSeriesMetric(timestamp=start_date + timedelta(days=i), value=5000.0)
            for i in range(7)
        ],
        response_times=[
            TimeSeriesMetric(timestamp=start_date + timedelta(days=i), value=150.0)
            for i in range(7)
        ],
        top_endpoints={
            "/api/threads": 500,
            "/api/messages": 300,
            "/api/files": 200,
        },
        error_rates={
            "/api/threads": 0.01,
            "/api/messages": 0.02,
            "/api/files": 0.015,
        },
    )


async def test_get_usage_statistics(
    app: FastAPI,
    client: AsyncClient,
    mock_analytics_service: AsyncMock,
    usage_statistics: UsageStatistics,
):
    """Test getting usage statistics."""
    # Setup
    mock_analytics_service.get_usage_statistics.return_value = usage_statistics

    # Execute
    response = await client.get("/analytics/usage")

    # Verify
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["metrics"]["total_requests"] == 1000
    assert data["metrics"]["total_threads"] == 50
    assert data["metrics"]["total_messages"] == 200
    assert data["metrics"]["total_tokens"] == 50000
    assert data["metrics"]["total_files"] == 25
    assert data["metrics"]["average_response_time"] == 150.5
    assert len(data["requests_over_time"]) == 7
    assert len(data["tokens_over_time"]) == 7
    assert len(data["response_times"]) == 7
    assert data["top_endpoints"]["/api/threads"] == 500
    assert data["error_rates"]["/api/threads"] == 0.01
    mock_analytics_service.get_usage_statistics.assert_called_once()


async def test_get_usage_statistics_invalid_dates(
    app: FastAPI,
    client: AsyncClient,
    mock_analytics_service: AsyncMock,
):
    """Test getting usage statistics with invalid date range."""
    # Setup
    end_date = datetime.utcnow()
    start_date = end_date + timedelta(days=1)  # Start date after end date

    # Execute
    response = await client.get(
        "/analytics/usage",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )

    # Verify
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Start date must be before end date"
    mock_analytics_service.get_usage_statistics.assert_not_called()


async def test_get_usage_statistics_service_error(
    app: FastAPI,
    client: AsyncClient,
    mock_analytics_service: AsyncMock,
):
    """Test getting usage statistics when service fails."""
    # Setup
    mock_analytics_service.get_usage_statistics.side_effect = Exception("Service error")

    # Execute
    response = await client.get("/analytics/usage")

    # Verify
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Failed to get usage statistics"
    mock_analytics_service.get_usage_statistics.assert_called_once()
