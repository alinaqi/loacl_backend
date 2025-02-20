"""
Suggestions service module.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import Depends

from app.core.logger import get_logger
from app.models.suggestions import FollowUpSuggestion
from app.repositories.suggestions import SuggestionsRepository
from app.services.base import BaseService
from app.services.conversation import ConversationContextService
from app.services.openai import OpenAIService

logger = get_logger(__name__)


def get_suggestions_repository() -> SuggestionsRepository:
    """Get suggestions repository instance."""
    return SuggestionsRepository()


class SuggestionsService(BaseService):
    """Service for managing follow-up suggestions."""

    def __init__(
        self,
        suggestions_repository: SuggestionsRepository = Depends(
            get_suggestions_repository
        ),
        conversation_service: ConversationContextService = Depends(),
        openai_service: OpenAIService = Depends(),
    ) -> None:
        """
        Initialize the service.

        Args:
            suggestions_repository: Repository for suggestions operations
            conversation_service: Service for conversation context
            openai_service: OpenAI service for generating suggestions
        """
        super().__init__()
        self.suggestions_repository = suggestions_repository
        self.conversation_service = conversation_service
        self.openai_service = openai_service

    async def generate_suggestions(
        self, thread_id: UUID, message_id: Optional[UUID] = None
    ) -> List[str]:
        """
        Generate follow-up suggestions for a thread.

        Args:
            thread_id: Thread ID
            message_id: Optional message ID to generate suggestions for

        Returns:
            List[str]: List of generated suggestions
        """
        try:
            # Get conversation context
            context = await self.conversation_service.get_conversation_context(
                thread_id=thread_id,
                message_id=message_id,
                window_size=5,  # Use last 5 messages for context
            )

            if not context:
                return []

            # Format context for OpenAI
            messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                }
                for msg in context
            ]

            # Generate suggestions using OpenAI
            response = await self.openai_service.create_completion(
                messages=messages,
                prompt="Based on this conversation, suggest 3 relevant follow-up questions that the user might want to ask.",
                max_tokens=150,
            )

            # Parse suggestions from response
            suggestions = [s.strip() for s in response.split("\n") if s.strip()][:3]

            # Store suggestions in database
            for suggestion in suggestions:
                await self.suggestions_repository.create(
                    FollowUpSuggestion(
                        thread_id=thread_id,
                        message_id=message_id,
                        suggestion=suggestion,
                    )
                )

            return suggestions

        except Exception as e:
            logger.error("Failed to generate suggestions", error=str(e))
            raise
