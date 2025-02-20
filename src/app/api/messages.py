"""
Message routes module.
"""

from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.models.response import NormalResponse, ResponseConfig, ResponseMode
from app.models.thread import Message, MessageCreate, MessageStatus
from app.services.conversation import ConversationContextService
from app.services.openai import OpenAIService

router = APIRouter(prefix="/threads", tags=["Messages"])


class MessageRequest(BaseModel):
    """Message request model."""

    content: str
    file_ids: Optional[List[str]] = None
    metadata: Optional[Dict] = None
    response_config: Optional[ResponseConfig] = None


class MessageListResponse(BaseModel):
    """Message list response model."""

    thread_id: UUID
    messages: List[Message]
    total: int
    has_more: bool
    metadata: Optional[Dict] = None


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


@router.get(
    "/{thread_id}/messages",
    response_model=MessageListResponse,
    responses={
        200: {"description": "Messages retrieved successfully"},
        404: {"description": "Thread not found"},
        500: {"description": "Internal server error"},
    },
)
async def list_messages(
    thread_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    ascending: bool = Query(default=False),
    status: Optional[MessageStatus] = None,
    conversation_service: ConversationContextService = Depends(),
) -> MessageListResponse:
    """
    Get messages from a thread with pagination.

    Args:
        thread_id: Thread ID
        limit: Maximum number of messages to return (1-100)
        offset: Number of messages to skip
        ascending: Sort messages in ascending order by creation date
        status: Filter messages by status
        conversation_service: Conversation context service

    Returns:
        MessageListResponse: List of messages with pagination info

    Raises:
        HTTPException: If thread not found or retrieval fails
    """
    try:
        # Get messages with pagination
        messages = await conversation_service.get_thread_messages(
            thread_id=thread_id,
            limit=limit + 1,  # Get one extra to check if there are more
            offset=offset,
            ascending=ascending,
            status=status,
        )

        # Check if there are more messages
        has_more = len(messages) > limit
        messages = messages[:limit]  # Remove the extra message if exists

        return MessageListResponse(
            thread_id=thread_id,
            messages=messages,
            total=len(messages),
            has_more=has_more,
            metadata={"offset": offset, "limit": limit},
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}",
        )
