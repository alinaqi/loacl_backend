"""
Health check service module.
"""

import os
import time
from typing import Dict

import psutil

from app.core.config import get_settings
from app.core.logger import get_logger
from app.models.health import DetailedServiceHealth, ServiceHealth, ServiceStatus
from app.services.base import BaseService

logger = get_logger(__name__)
settings = get_settings()

# Start time of the service
START_TIME = time.time()


class HealthService(BaseService):
    """Service for health checks."""

    def __init__(self):
        """Initialize the service."""
        super().__init__()
        self.version = settings.version

    async def get_basic_health(self) -> ServiceHealth:
        """
        Get basic health status.

        Returns:
            ServiceHealth: Basic health status
        """
        try:
            # Calculate uptime
            uptime = time.time() - START_TIME

            return ServiceHealth(
                status=ServiceStatus.HEALTHY,
                version=self.version,
                uptime=uptime,
            )
        except Exception as e:
            logger.error("Failed to get basic health status", error=str(e))
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY,
                version=self.version,
                uptime=0,
            )

    async def get_detailed_health(self) -> DetailedServiceHealth:
        """
        Get detailed health status.

        Returns:
            DetailedServiceHealth: Detailed health status
        """
        try:
            # Get basic health first
            basic_health = await self.get_basic_health()

            # Get system metrics
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            # Get database latency (simulated for now)
            db_latency = await self._check_database_latency()

            # Get connection info
            connections = len(process.connections())

            # Build detailed health
            return DetailedServiceHealth(
                status=basic_health.status,
                version=basic_health.version,
                uptime=basic_health.uptime,
                database_latency=db_latency,
                memory_usage=memory_info.rss / 1024 / 1024,  # Convert to MB
                cpu_usage=cpu_percent,
                open_connections=connections,
                active_requests=await self._get_active_requests(),
                dependencies=await self._check_dependencies(),
                metrics={
                    "thread_count": len(process.threads()),
                    "open_files": len(process.open_files()),
                },
            )
        except Exception as e:
            logger.error("Failed to get detailed health status", error=str(e))
            return DetailedServiceHealth(
                status=ServiceStatus.UNHEALTHY,
                version=self.version,
                uptime=0,
                database_latency=0,
                memory_usage=0,
                cpu_usage=0,
                open_connections=0,
                active_requests=0,
                last_error=str(e),
            )

    async def _check_database_latency(self) -> float:
        """
        Check database latency.

        Returns:
            float: Database latency in milliseconds
        """
        try:
            start_time = time.time()
            # Simple ping to database
            await self.db.rpc("ping").execute()
            return (time.time() - start_time) * 1000  # Convert to milliseconds
        except Exception as e:
            logger.error("Failed to check database latency", error=str(e))
            return 0

    async def _get_active_requests(self) -> int:
        """
        Get number of active requests.

        Returns:
            int: Number of active requests
        """
        # This would need to be implemented based on your request tracking system
        # For now, return a placeholder value
        return 0

    async def _check_dependencies(self) -> Dict[str, ServiceStatus]:
        """
        Check status of external dependencies.

        Returns:
            Dict[str, ServiceStatus]: Status of each dependency
        """
        dependencies = {}

        # Check database
        try:
            await self.db.rpc("ping").execute()
            dependencies["database"] = ServiceStatus.HEALTHY
        except Exception:
            dependencies["database"] = ServiceStatus.UNHEALTHY

        # Add other dependency checks as needed
        # For example: Redis, OpenAI, etc.

        return dependencies
