"""
Analytics service module.
"""

from datetime import datetime, timedelta
from typing import Dict, List

from app.core.logger import get_logger
from app.models.analytics import TimeSeriesMetric, UsageMetrics, UsageStatistics
from app.services.base import BaseService

logger = get_logger(__name__)


class AnalyticsService(BaseService):
    """Service for analytics operations."""

    async def get_usage_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> UsageStatistics:
        """
        Get usage statistics for a given time period.

        Args:
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            UsageStatistics: Usage statistics for the period
        """
        try:
            # Get basic metrics
            metrics = await self._get_usage_metrics(start_date, end_date)

            # Get time series data
            requests = await self._get_requests_over_time(start_date, end_date)
            tokens = await self._get_tokens_over_time(start_date, end_date)
            response_times = await self._get_response_times(start_date, end_date)

            # Get endpoint statistics
            top_endpoints = await self._get_top_endpoints(start_date, end_date)
            error_rates = await self._get_error_rates(start_date, end_date)

            return UsageStatistics(
                start_date=start_date,
                end_date=end_date,
                metrics=metrics,
                requests_over_time=requests,
                tokens_over_time=tokens,
                response_times=response_times,
                top_endpoints=top_endpoints,
                error_rates=error_rates,
            )
        except Exception as e:
            logger.error("Failed to get usage statistics", error=str(e))
            raise

    async def _get_usage_metrics(
        self, start_date: datetime, end_date: datetime
    ) -> UsageMetrics:
        """
        Get basic usage metrics.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            UsageMetrics: Basic usage metrics
        """
        try:
            # Get total requests
            requests_result = await self.db.rpc(
                "get_total_requests",
                {"start_date": start_date, "end_date": end_date},
            ).execute()
            total_requests = (
                requests_result.data[0]["count"] if requests_result.data else 0
            )

            # Get total threads
            threads_result = await self.db.rpc(
                "get_total_threads",
                {"start_date": start_date, "end_date": end_date},
            ).execute()
            total_threads = (
                threads_result.data[0]["count"] if threads_result.data else 0
            )

            # Get total messages
            messages_result = await self.db.rpc(
                "get_total_messages",
                {"start_date": start_date, "end_date": end_date},
            ).execute()
            total_messages = (
                messages_result.data[0]["count"] if messages_result.data else 0
            )

            # Get total tokens
            tokens_result = await self.db.rpc(
                "get_total_tokens",
                {"start_date": start_date, "end_date": end_date},
            ).execute()
            total_tokens = tokens_result.data[0]["sum"] if tokens_result.data else 0

            # Get total files
            files_result = await self.db.rpc(
                "get_total_files",
                {"start_date": start_date, "end_date": end_date},
            ).execute()
            total_files = files_result.data[0]["count"] if files_result.data else 0

            # Get average response time
            response_time_result = await self.db.rpc(
                "get_average_response_time",
                {"start_date": start_date, "end_date": end_date},
            ).execute()
            avg_response_time = (
                response_time_result.data[0]["avg"] if response_time_result.data else 0
            )

            return UsageMetrics(
                total_requests=total_requests,
                total_threads=total_threads,
                total_messages=total_messages,
                total_tokens=total_tokens,
                total_files=total_files,
                average_response_time=avg_response_time,
            )
        except Exception as e:
            logger.error("Failed to get usage metrics", error=str(e))
            raise

    async def _get_requests_over_time(
        self, start_date: datetime, end_date: datetime
    ) -> List[TimeSeriesMetric]:
        """
        Get requests over time.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            List[TimeSeriesMetric]: Requests over time
        """
        try:
            result = await self.db.rpc(
                "get_requests_over_time",
                {"start_date": start_date, "end_date": end_date},
            ).execute()

            return [
                TimeSeriesMetric(timestamp=row["timestamp"], value=row["count"])
                for row in result.data
            ]
        except Exception as e:
            logger.error("Failed to get requests over time", error=str(e))
            raise

    async def _get_tokens_over_time(
        self, start_date: datetime, end_date: datetime
    ) -> List[TimeSeriesMetric]:
        """
        Get token usage over time.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            List[TimeSeriesMetric]: Token usage over time
        """
        try:
            result = await self.db.rpc(
                "get_tokens_over_time",
                {"start_date": start_date, "end_date": end_date},
            ).execute()

            return [
                TimeSeriesMetric(timestamp=row["timestamp"], value=row["sum"])
                for row in result.data
            ]
        except Exception as e:
            logger.error("Failed to get tokens over time", error=str(e))
            raise

    async def _get_response_times(
        self, start_date: datetime, end_date: datetime
    ) -> List[TimeSeriesMetric]:
        """
        Get response times over time.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            List[TimeSeriesMetric]: Response times over time
        """
        try:
            result = await self.db.rpc(
                "get_response_times",
                {"start_date": start_date, "end_date": end_date},
            ).execute()

            return [
                TimeSeriesMetric(timestamp=row["timestamp"], value=row["avg"])
                for row in result.data
            ]
        except Exception as e:
            logger.error("Failed to get response times", error=str(e))
            raise

    async def _get_top_endpoints(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """
        Get most frequently accessed endpoints.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Dict[str, int]: Endpoint access counts
        """
        try:
            result = await self.db.rpc(
                "get_top_endpoints",
                {"start_date": start_date, "end_date": end_date},
            ).execute()

            return {row["endpoint"]: row["count"] for row in result.data}
        except Exception as e:
            logger.error("Failed to get top endpoints", error=str(e))
            raise

    async def _get_error_rates(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, float]:
        """
        Get error rates by endpoint.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            Dict[str, float]: Error rates by endpoint
        """
        try:
            result = await self.db.rpc(
                "get_error_rates",
                {"start_date": start_date, "end_date": end_date},
            ).execute()

            return {row["endpoint"]: row["error_rate"] for row in result.data}
        except Exception as e:
            logger.error("Failed to get error rates", error=str(e))
            raise
