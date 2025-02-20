"""
Health check endpoints module.
"""

from fastapi import APIRouter, Depends

from app.core.logger import get_logger
from app.models.health import DetailedServiceHealth, ServiceHealth
from app.services.health import HealthService

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=ServiceHealth)
async def get_health(
    health_service: HealthService = Depends(),
) -> ServiceHealth:
    """
    Get basic health status.

    Returns:
        ServiceHealth: Basic health status
    """
    return await health_service.get_basic_health()


@router.get("/health/detailed", response_model=DetailedServiceHealth)
async def get_detailed_health(
    health_service: HealthService = Depends(),
) -> DetailedServiceHealth:
    """
    Get detailed health status.

    Returns:
        DetailedServiceHealth: Detailed health status
    """
    return await health_service.get_detailed_health()
