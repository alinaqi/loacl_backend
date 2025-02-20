"""
Message routes module.
"""

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.models.response import NormalResponse, ResponseConfig, ResponseMode
from app.models.thread import Message, MessageCreate
from app.services.conversation import ConversationContextService
from app.services.openai import OpenAIService

router = APIRouter(prefix="/threads", tags=["Messages"])


class MessageRequest(BaseModel):
    """Message request model."""

    content: str
    file_ids: Optional[List[str]] = None
    metadata: Optional[Dict] = None
    response_config: Optional[ResponseConfig] = None


@router.post(
    "/{thread_id}/messages",
    response_model=NormalResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Message created successfully"},
        404: {"description": "Thread not found"},
        500: {"description": "Internal server error"},
    },
)
async def create_message(
    thread_id: UUID,
    request: MessageRequest,
    openai_service: OpenAIService = Depends(),
    conversation_service: ConversationContextService = Depends(),
) -> NormalResponse:
    """
    Create a new message in a thread.

    Args:
        thread_id: Thread ID
        request: Message request
        openai_service: OpenAI service
        conversation_service: Conversation context service

    Returns:
        NormalResponse: Created message response

    Raises:
        HTTPException: If thread not found or message creation fails
    """
    try:
        # Get conversation context
        context = await conversation_service.get_conversation_context(thread_id)

        # Create message
        message = MessageCreate(
            content=request.content,
            file_ids=request.file_ids or [],
            metadata=request.metadata or {},
        )

        # Get response mode from config or default to normal
        response_mode = (
            request.response_config.mode
            if request.response_config
            else ResponseMode.NORMAL
        )

        # Create message in OpenAI thread
        response = await openai_service.create_message(
            thread_id=str(thread_id),
            content=message.content,
            file_ids=message.file_ids,
            metadata=message.metadata,
        )

        return NormalResponse(
            thread_id=thread_id,
            message_id=UUID(response.id),
            content=response.content[0].text.value,
            metadata=response.metadata,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create message: {str(e)}",
        )
