"""
Event models module.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.models.base import BaseModelTimestamps


class EventType(str, Enum):
    """Event type enumeration."""

    THREAD_CREATED = "thread.created"
    THREAD_UPDATED = "thread.updated"
    THREAD_DELETED = "thread.deleted"
    MESSAGE_CREATED = "message.created"
    MESSAGE_UPDATED = "message.updated"
    MESSAGE_DELETED = "message.deleted"
    FILE_UPLOADED = "file.uploaded"
    FILE_DELETED = "file.deleted"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"


class WebhookStatus(str, Enum):
    """Webhook status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""

    url: HttpUrl = Field(..., description="The URL to send webhook events to")
    events: List[EventType] = Field(..., description="List of events to subscribe to")
    description: Optional[str] = Field(
        None, description="Optional description of the webhook"
    )
    metadata: Optional[Dict] = Field(
        default_factory=dict, description="Optional metadata"
    )
    secret: Optional[str] = Field(
        None, description="Secret for signing webhook payloads"
    )


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""

    url: Optional[HttpUrl] = Field(
        None, description="The URL to send webhook events to"
    )
    events: Optional[List[EventType]] = Field(
        None, description="List of events to subscribe to"
    )
    description: Optional[str] = Field(
        None, description="Optional description of the webhook"
    )
    metadata: Optional[Dict] = Field(None, description="Optional metadata")
    secret: Optional[str] = Field(
        None, description="Secret for signing webhook payloads"
    )
    status: Optional[WebhookStatus] = Field(None, description="Status of the webhook")


class Webhook(BaseModelTimestamps):
    """Webhook model."""

    id: UUID = Field(..., description="Unique identifier for the webhook")
    url: HttpUrl = Field(..., description="The URL to send webhook events to")
    events: List[EventType] = Field(..., description="List of events to subscribe to")
    description: Optional[str] = Field(
        None, description="Optional description of the webhook"
    )
    metadata: Dict = Field(default_factory=dict, description="Optional metadata")
    secret: Optional[str] = Field(
        None, description="Secret for signing webhook payloads"
    )
    status: WebhookStatus = Field(
        default=WebhookStatus.ACTIVE, description="Status of the webhook"
    )
    last_delivery_at: Optional[datetime] = Field(
        None, description="Timestamp of last successful delivery"
    )
    failure_count: int = Field(
        default=0, description="Number of consecutive delivery failures"
    )


class EventPayload(BaseModel):
    """Base event payload model."""

    id: UUID = Field(..., description="Unique identifier for the event")
    type: EventType = Field(..., description="Type of the event")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the event occurred"
    )
    data: Dict = Field(..., description="Event-specific data")
    metadata: Dict = Field(default_factory=dict, description="Optional metadata")
