"""
Event service module.
"""

import hashlib
import hmac
import json
from typing import Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from fastapi import BackgroundTasks

from app.core.logger import get_logger
from app.models.events import EventPayload, EventType, Webhook
from app.repositories.webhook import WebhookRepository
from app.services.base import BaseService

logger = get_logger(__name__)


class EventService(BaseService):
    """Service for handling events and webhooks."""

    def __init__(self, webhook_repository: WebhookRepository):
        """
        Initialize the service.

        Args:
            webhook_repository: Repository for webhook operations
        """
        super().__init__()
        self.webhook_repository = webhook_repository
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def dispatch_event(
        self,
        background_tasks: BackgroundTasks,
        event_type: EventType,
        data: Dict,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Dispatch an event to all registered webhooks.

        Args:
            background_tasks: FastAPI background tasks
            event_type: Type of event
            data: Event data
            metadata: Optional metadata
        """
        try:
            # Create event payload
            event = EventPayload(
                id=uuid4(),
                type=event_type,
                data=data,
                metadata=metadata or {},
            )

            # Get active webhooks for this event type
            webhooks = await self.webhook_repository.get_active_webhooks(event_type)

            # Add delivery task for each webhook
            for webhook in webhooks:
                background_tasks.add_task(
                    self._deliver_webhook,
                    webhook=webhook,
                    payload=event,
                )

        except Exception as e:
            logger.error("Failed to dispatch event", error=str(e))
            raise

    async def _deliver_webhook(self, webhook: Webhook, payload: EventPayload) -> None:
        """
        Deliver a webhook payload.

        Args:
            webhook: Webhook to deliver to
            payload: Event payload
        """
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "LOACL-Webhook/1.0",
                "X-LOACL-Event": payload.type,
                "X-LOACL-Delivery": str(payload.id),
            }

            # Sign payload if secret is set
            if webhook.secret:
                signature = self._sign_payload(webhook.secret, payload)
                headers["X-LOACL-Signature"] = signature

            # Send webhook
            response = await self.http_client.post(
                str(webhook.url),
                json=payload.model_dump(),
                headers=headers,
            )

            # Update webhook status
            await self.webhook_repository.update_delivery_status(
                webhook.id,
                success=response.is_success,
                error=str(response.text) if not response.is_success else None,
            )

        except Exception as e:
            logger.error("Failed to deliver webhook", error=str(e))
            await self.webhook_repository.update_delivery_status(
                webhook.id,
                success=False,
                error=str(e),
            )

    def _sign_payload(self, secret: str, payload: EventPayload) -> str:
        """
        Sign a webhook payload.

        Args:
            secret: Webhook secret
            payload: Event payload

        Returns:
            str: HMAC signature
        """
        payload_data = json.dumps(payload.model_dump(), sort_keys=True)
        return hmac.new(
            secret.encode(),
            payload_data.encode(),
            hashlib.sha256,
        ).hexdigest()
