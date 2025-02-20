"""
Task models module.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import BaseModelTimestamps


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCreate(BaseModel):
    """Schema for creating a task."""

    name: str = Field(..., description="Name of the task")
    task_type: str = Field(..., description="Type of task to execute")
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL, description="Task priority"
    )
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task payload")
    scheduled_for: Optional[datetime] = Field(
        None, description="When to execute the task"
    )
    timeout: Optional[int] = Field(None, description="Task timeout in seconds")
    retry_count: Optional[int] = Field(None, description="Number of retries on failure")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    status: Optional[TaskStatus] = Field(None, description="Task status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[datetime] = Field(None, description="When the task started")
    completed_at: Optional[datetime] = Field(
        None, description="When the task completed"
    )
    retry_count: Optional[int] = Field(None, description="Current retry count")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")


class Task(BaseModelTimestamps):
    """Task model."""

    id: UUID = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the task")
    task_type: str = Field(..., description="Type of task to execute")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status")
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL, description="Task priority"
    )
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task payload")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    scheduled_for: Optional[datetime] = Field(
        None, description="When to execute the task"
    )
    started_at: Optional[datetime] = Field(None, description="When the task started")
    completed_at: Optional[datetime] = Field(
        None, description="When the task completed"
    )
    timeout: Optional[int] = Field(None, description="Task timeout in seconds")
    retry_count: int = Field(default=0, description="Current retry count")
    max_retries: Optional[int] = Field(None, description="Maximum number of retries")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
