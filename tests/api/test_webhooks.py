"""
Tests for webhook endpoints.
"""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette import status

from app.models.events import EventType, Webhook, WebhookCreate, WebhookStatus


@pytest.fixture
def webhook_id() -> UUID:
    """Fixture for webhook ID."""
    return uuid4()


@pytest.fixture
def webhook_create() -> WebhookCreate:
    """Fixture for webhook creation data."""
    return WebhookCreate(
        url="https://example.com/webhook",
        events=[EventType.THREAD_CREATED, EventType.MESSAGE_CREATED],
        description="Test webhook",
        secret="test-secret",
    )


@pytest.fixture
def webhook(webhook_id: UUID, webhook_create: WebhookCreate) -> Webhook:
    """Fixture for webhook data."""
    return Webhook(
        id=webhook_id,
        url=webhook_create.url,
        events=webhook_create.events,
        description=webhook_create.description,
        secret=webhook_create.secret,
        status=WebhookStatus.ACTIVE,
    )


async def test_create_webhook(
    app: FastAPI,
    client: AsyncClient,
    webhook_create: WebhookCreate,
    webhook: Webhook,
    mock_webhook_repository: AsyncMock,
):
    """Test creating a webhook."""
    # Setup
    mock_webhook_repository.create.return_value = webhook

    # Execute
    response = await client.post("/webhooks", json=webhook_create.model_dump())

    # Verify
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["id"] == str(webhook.id)
    assert response.json()["url"] == str(webhook.url)
    mock_webhook_repository.create.assert_called_once_with(webhook_create)


async def test_list_webhooks(
    app: FastAPI,
    client: AsyncClient,
    webhook: Webhook,
    mock_webhook_repository: AsyncMock,
):
    """Test listing webhooks."""
    # Setup
    mock_webhook_repository.list.return_value = [webhook]

    # Execute
    response = await client.get("/webhooks")

    # Verify
    assert response.status_code == status.HTTP_200_OK
    webhooks = response.json()
    assert len(webhooks) == 1
    assert webhooks[0]["id"] == str(webhook.id)
    assert webhooks[0]["url"] == str(webhook.url)
    mock_webhook_repository.list.assert_called_once()


async def test_delete_webhook(
    app: FastAPI,
    client: AsyncClient,
    webhook_id: UUID,
    webhook: Webhook,
    mock_webhook_repository: AsyncMock,
):
    """Test deleting a webhook."""
    # Setup
    mock_webhook_repository.get.return_value = webhook
    mock_webhook_repository.delete.return_value = None

    # Execute
    response = await client.delete(f"/webhooks/{webhook_id}")

    # Verify
    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_webhook_repository.get.assert_called_once_with(webhook_id)
    mock_webhook_repository.delete.assert_called_once_with(webhook_id)


async def test_delete_webhook_not_found(
    app: FastAPI,
    client: AsyncClient,
    webhook_id: UUID,
    mock_webhook_repository: AsyncMock,
):
    """Test deleting a non-existent webhook."""
    # Setup
    mock_webhook_repository.get.return_value = None

    # Execute
    response = await client.delete(f"/webhooks/{webhook_id}")

    # Verify
    assert response.status_code == status.HTTP_404_NOT_FOUND
    mock_webhook_repository.get.assert_called_once_with(webhook_id)
    mock_webhook_repository.delete.assert_not_called()
