"""
Webhook endpoints module.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.core.logger import get_logger
from app.models.events import Webhook, WebhookCreate, WebhookUpdate
from app.models.user import User
from app.repositories.webhook import WebhookRepository
from app.services.events import EventService

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=Webhook, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook: WebhookCreate,
    current_user: User = Depends(get_current_user),
    webhook_repository: WebhookRepository = Depends(),
) -> Webhook:
    """
    Register a new webhook.

    Args:
        webhook: Webhook configuration
        current_user: Current authenticated user
        webhook_repository: Webhook repository instance

    Returns:
        Webhook: Created webhook
    """
    try:
        return await webhook_repository.create(webhook)
    except Exception as e:
        logger.error("Failed to create webhook", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create webhook",
        )


@router.get("", response_model=List[Webhook])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    webhook_repository: WebhookRepository = Depends(),
) -> List[Webhook]:
    """
    List all registered webhooks.

    Args:
        current_user: Current authenticated user
        webhook_repository: Webhook repository instance

    Returns:
        List[Webhook]: List of registered webhooks
    """
    try:
        return await webhook_repository.list()
    except Exception as e:
        logger.error("Failed to list webhooks", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhooks",
        )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    webhook_repository: WebhookRepository = Depends(),
) -> None:
    """
    Delete a webhook.

    Args:
        webhook_id: ID of the webhook to delete
        current_user: Current authenticated user
        webhook_repository: Webhook repository instance
    """
    try:
        # Check if webhook exists
        webhook = await webhook_repository.get(webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found",
            )

        # Delete webhook
        await webhook_repository.delete(webhook_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete webhook", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook",
        )
