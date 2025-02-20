"""
Tests for the event system.
"""

import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import BackgroundTasks

from app.models.events import EventPayload, EventType, Webhook, WebhookStatus
from app.repositories.webhook import WebhookRepository
from app.services.events import EventService


@pytest.fixture
def webhook_repository():
    """Create a mock webhook repository."""
    return AsyncMock(spec=WebhookRepository)


@pytest.fixture
def event_service(webhook_repository):
    """Create an event service instance."""
    return EventService(webhook_repository=webhook_repository)


@pytest.fixture
def sample_webhook():
    """Create a sample webhook."""
    return Webhook(
        id=uuid4(),
        url="https://example.com/webhook",
        events=[EventType.THREAD_CREATED, EventType.MESSAGE_CREATED],
        description="Test webhook",
        secret="test-secret",
        status=WebhookStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_event():
    """Create a sample event."""
    return EventPayload(
        id=uuid4(),
        type=EventType.THREAD_CREATED,
        data={"thread_id": str(uuid4())},
        metadata={"user_id": str(uuid4())},
    )


async def test_dispatch_event(event_service, webhook_repository, sample_webhook):
    """Test dispatching an event."""
    # Setup
    webhook_repository.get_active_webhooks.return_value = [sample_webhook]
    background_tasks = BackgroundTasks()

    # Execute
    await event_service.dispatch_event(
        background_tasks=background_tasks,
        event_type=EventType.THREAD_CREATED,
        data={"thread_id": str(uuid4())},
    )

    # Verify
    webhook_repository.get_active_webhooks.assert_called_once_with(
        EventType.THREAD_CREATED
    )
    assert len(background_tasks.tasks) == 1


@pytest.mark.asyncio
async def test_deliver_webhook_success(
    event_service, webhook_repository, sample_webhook, sample_event
):
    """Test successful webhook delivery."""
    # Setup
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.is_success = True

    with patch.object(event_service.http_client, "post", return_value=mock_response):
        # Execute
        await event_service._deliver_webhook(sample_webhook, sample_event)

        # Verify
        webhook_repository.update_delivery_status.assert_called_once_with(
            sample_webhook.id,
            success=True,
            error=None,
        )


@pytest.mark.asyncio
async def test_deliver_webhook_failure(
    event_service, webhook_repository, sample_webhook, sample_event
):
    """Test failed webhook delivery."""
    # Setup
    mock_response = AsyncMock(spec=httpx.Response)
    mock_response.is_success = False
    mock_response.text = "Failed to deliver"

    with patch.object(event_service.http_client, "post", return_value=mock_response):
        # Execute
        await event_service._deliver_webhook(sample_webhook, sample_event)

        # Verify
        webhook_repository.update_delivery_status.assert_called_once_with(
            sample_webhook.id,
            success=False,
            error="Failed to deliver",
        )


def test_sign_payload(event_service, sample_event):
    """Test webhook payload signing."""
    # Setup
    secret = "test-secret"
    expected_signature = hmac.new(
        secret.encode(),
        json.dumps(sample_event.model_dump(), sort_keys=True).encode(),
        hashlib.sha256,
    ).hexdigest()

    # Execute
    signature = event_service._sign_payload(secret, sample_event)

    # Verify
    assert signature == expected_signature
