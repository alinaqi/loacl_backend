"""
Analytics endpoints module.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status

from app.core.dependencies import get_current_user
from app.core.logger import get_logger
from app.models.analytics import UsageStatistics
from app.models.user import User
from app.services.analytics import AnalyticsService

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/usage", response_model=UsageStatistics)
async def get_usage_statistics(
    start_date: datetime = Query(
        default_factory=lambda: datetime.utcnow() - timedelta(days=7),
        description="Start date for statistics (default: 7 days ago)",
    ),
    end_date: datetime = Query(
        default_factory=datetime.utcnow,
        description="End date for statistics (default: now)",
    ),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(),
) -> UsageStatistics:
    """
    Get usage statistics for a given time period.

    Args:
        start_date: Start date for statistics
        end_date: End date for statistics
        current_user: Current authenticated user
        analytics_service: Analytics service instance

    Returns:
        UsageStatistics: Usage statistics for the period
    """
    try:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date",
            )

        # Get statistics
        return await analytics_service.get_usage_statistics(start_date, end_date)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get usage statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage statistics",
        )
