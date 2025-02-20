"""
Health check models module.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    """Service status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceHealth(BaseModel):
    """Service health model."""

    status: ServiceStatus = Field(..., description="Current status of the service")
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., description="Service uptime in seconds")


class DetailedServiceHealth(ServiceHealth):
    """Detailed service health model."""

    database_latency: float = Field(..., description="Database latency in milliseconds")
    memory_usage: float = Field(..., description="Memory usage in megabytes")
    cpu_usage: float = Field(..., description="CPU usage percentage")
    open_connections: int = Field(..., description="Number of open connections")
    active_requests: int = Field(..., description="Number of active requests")
    last_error: Optional[str] = Field(None, description="Last error message if any")
    dependencies: Dict[str, ServiceStatus] = Field(
        default_factory=dict, description="Status of external dependencies"
    )
    metrics: Dict[str, float] = Field(
        default_factory=dict, description="Additional metrics"
    )
