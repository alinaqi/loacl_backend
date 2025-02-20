"""
Webhook repository module.
"""

from typing import List, Optional
from uuid import UUID

from app.core.logger import get_logger
from app.models.events import Webhook, WebhookCreate, WebhookUpdate
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class WebhookRepository(BaseRepository[Webhook, WebhookCreate, WebhookUpdate]):
    """Repository for webhook operations."""

    def __init__(self):
        """Initialize the repository."""
        super().__init__("webhooks", Webhook)

    async def get_active_webhooks(self, event_type: str) -> List[Webhook]:
        """
        Get all active webhooks for a specific event type.

        Args:
            event_type: Type of event to get webhooks for

        Returns:
            List[Webhook]: List of active webhooks
        """
        try:
            response = (
                await self.client.table(self.table_name)
                .select("*")
                .eq("status", "active")
                .execute()
            )
            webhooks = [Webhook(**webhook) for webhook in response.data]
            return [webhook for webhook in webhooks if event_type in webhook.events]
        except Exception as e:
            logger.error("Failed to get active webhooks", error=str(e))
            raise

    async def update_delivery_status(
        self, webhook_id: UUID, success: bool, error: Optional[str] = None
    ) -> None:
        """
        Update webhook delivery status.

        Args:
            webhook_id: Webhook ID
            success: Whether delivery was successful
            error: Optional error message
        """
        try:
            webhook = await self.get(webhook_id)
            if not webhook:
                return

            update_data = {
                "last_delivery_at": "NOW()" if success else webhook.last_delivery_at,
                "failure_count": 0 if success else webhook.failure_count + 1,
                "status": (
                    webhook.status
                    if success
                    else "failed" if webhook.failure_count >= 5 else webhook.status
                ),
                "metadata": {
                    **webhook.metadata,
                    "last_error": error if error else None,
                },
            }

            await self.update(webhook_id, WebhookUpdate(**update_data))
        except Exception as e:
            logger.error("Failed to update webhook delivery status", error=str(e))
            raise
