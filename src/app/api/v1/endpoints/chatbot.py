from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.chatbot import (
    ChatbotCreate,
    ChatbotResponse,
    ChatbotUpdate,
    ChatbotAnalytics,
    ChatbotStatusUpdate,
    ChatbotEmbedCode
)
from app.services.chatbot import ChatbotService
from app.models.user import User

router = APIRouter()

@router.post("", response_model=ChatbotResponse)
async def create_chatbot(
    chatbot: ChatbotCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> ChatbotResponse:
    """
    Create a new chatbot.
    """
    service = ChatbotService(db)
    return await service.create_chatbot(chatbot, current_user.id)

@router.get("", response_model=List[ChatbotResponse])
async def list_chatbots(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> List[ChatbotResponse]:
    """
    List all chatbots for the current user.
    """
    service = ChatbotService(db)
    return await service.get_chatbots(current_user.id)

@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> ChatbotResponse:
    """
    Get a specific chatbot by ID.
    """
    service = ChatbotService(db)
    chatbot = await service.get_chatbot(chatbot_id, current_user.id)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return chatbot

@router.put("/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: UUID,
    chatbot_update: ChatbotUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> ChatbotResponse:
    """
    Update a chatbot.
    """
    service = ChatbotService(db)
    updated_chatbot = await service.update_chatbot(
        chatbot_id,
        chatbot_update,
        current_user.id
    )
    if not updated_chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return updated_chatbot

@router.delete("/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatbot(
    chatbot_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete a chatbot.
    """
    service = ChatbotService(db)
    deleted = await service.delete_chatbot(chatbot_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )

@router.patch("/{chatbot_id}/status", response_model=ChatbotResponse)
async def update_chatbot_status(
    chatbot_id: UUID,
    status_update: ChatbotStatusUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> ChatbotResponse:
    """
    Toggle chatbot active status.
    """
    service = ChatbotService(db)
    updated_chatbot = await service.update_chatbot_status(
        chatbot_id,
        status_update.is_active,
        current_user.id
    )
    if not updated_chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return updated_chatbot

@router.get("/{chatbot_id}/analytics", response_model=ChatbotAnalytics)
async def get_chatbot_analytics(
    chatbot_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> ChatbotAnalytics:
    """
    Get analytics for a specific chatbot.
    """
    service = ChatbotService(db)
    # First verify chatbot exists and belongs to user
    chatbot = await service.get_chatbot(chatbot_id, current_user.id)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return await service.get_chatbot_analytics(chatbot_id, current_user.id)

@router.post("/{chatbot_id}/validate")
async def validate_credentials(
    chatbot_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> dict:
    """
    Validate OpenAI credentials for a chatbot.
    """
    service = ChatbotService(db)
    # First verify chatbot exists and belongs to user
    chatbot = await service.get_chatbot(chatbot_id, current_user.id)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    is_valid = await service.validate_openai_credentials(chatbot_id, current_user.id)
    return {"is_valid": is_valid}

@router.get("/{chatbot_id}/embed", response_model=ChatbotEmbedCode)
async def get_embed_code(
    chatbot_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
) -> ChatbotEmbedCode:
    """
    Get embed code for a chatbot.
    """
    service = ChatbotService(db)
    # First verify chatbot exists and belongs to user
    chatbot = await service.get_chatbot(chatbot_id, current_user.id)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found"
        )
    return ChatbotEmbedCode(**service.generate_embed_code(chatbot_id)) 