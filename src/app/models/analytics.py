"""
Analytics models module.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UsageMetrics(BaseModel):
    """Usage metrics model."""

    total_requests: int = Field(..., description="Total number of API requests")
    total_threads: int = Field(..., description="Total number of threads created")
    total_messages: int = Field(..., description="Total number of messages sent")
    total_tokens: int = Field(..., description="Total number of tokens used")
    total_files: int = Field(..., description="Total number of files uploaded")
    average_response_time: float = Field(
        ..., description="Average response time in milliseconds"
    )


class TimeSeriesMetric(BaseModel):
    """Time series metric model."""

    timestamp: datetime = Field(..., description="Timestamp of the metric")
    value: float = Field(..., description="Value of the metric")


class UsageStatistics(BaseModel):
    """Usage statistics model."""

    start_date: datetime = Field(..., description="Start date of the statistics")
    end_date: datetime = Field(..., description="End date of the statistics")
    metrics: UsageMetrics = Field(..., description="Current usage metrics")
    requests_over_time: List[TimeSeriesMetric] = Field(
        ..., description="API requests over time"
    )
    tokens_over_time: List[TimeSeriesMetric] = Field(
        ..., description="Token usage over time"
    )
    response_times: List[TimeSeriesMetric] = Field(
        ..., description="Response times over time"
    )
    top_endpoints: Dict[str, int] = Field(
        ..., description="Most frequently accessed endpoints"
    )
    error_rates: Dict[str, float] = Field(..., description="Error rates by endpoint")
