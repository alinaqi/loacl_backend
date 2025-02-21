from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api import deps
from app.schemas.user import User
from app.services.assistant import AssistantService

router = APIRouter()


class ThemeSettings(BaseModel):
    primary_color: str = Field(default="#4F46E5")
    secondary_color: str = Field(default="#6366F1")
    text_color: str = Field(default="#111827")
    background_color: str = Field(default="#FFFFFF")


class LayoutSettings(BaseModel):
    width: str = Field(default="380px")
    height: str = Field(default="600px")
    position: str = Field(default="right")
    bubble_icon: Optional[str] = None


class TypographySettings(BaseModel):
    font_family: str = Field(default="Inter, system-ui, sans-serif")
    font_size: str = Field(default="14px")


class DesignSettings(BaseModel):
    theme: ThemeSettings = Field(default_factory=ThemeSettings)
    layout: LayoutSettings = Field(default_factory=LayoutSettings)
    typography: TypographySettings = Field(default_factory=TypographySettings)


class Features(BaseModel):
    showFileUpload: bool = Field(default=True)
    showVoiceInput: bool = Field(default=True)
    showEmoji: bool = Field(default=True)
    showGuidedQuestions: bool = Field(default=True)
    showFollowUpSuggestions: bool = Field(default=True)


class AssistantCreate(BaseModel):
    name: str = Field(..., description="Name of the assistant")
    description: Optional[str] = None
    instructions: Optional[str] = None
    model: str = Field(default="gpt-4-turbo-preview")
    api_key: str = Field(..., description="OpenAI API key")
    assistant_id: str = Field(..., description="OpenAI Assistant ID")
    tools_enabled: List[str] = Field(default_factory=list)
    design_settings: DesignSettings = Field(default_factory=DesignSettings)
    features: Features = Field(default_factory=Features)
    is_active: bool = Field(default=True)


class AssistantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    tools_enabled: Optional[List[str]] = None
    design_settings: Optional[DesignSettings] = None
    features: Optional[Features] = None
    is_active: Optional[bool] = None


class AssistantResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    instructions: Optional[str]
    model: str
    tools_enabled: List[str]
    design_settings: DesignSettings
    features: Features
    is_active: bool
    created_at: str
    updated_at: str


class AssistantAnalytics(BaseModel):
    total_conversations: int
    total_messages: int
    average_response_time: float
    user_satisfaction_rate: Optional[float]
    most_common_topics: List[str]


class EmbedSettings(BaseModel):
    """Settings for embedding the assistant in a website."""

    allowed_domains: List[str] = Field(
        default_factory=list,
        description="List of domains where the assistant can be embedded",
    )
    custom_styles: Optional[str] = Field(
        None, description="Custom CSS styles for the embedded assistant"
    )
    custom_script: Optional[str] = Field(
        None, description="Custom JavaScript for the embedded assistant"
    )
    position: str = Field(
        default="right",
        description="Position of the assistant widget (right, left, center)",
    )
    auto_open: bool = Field(
        default=False,
        description="Whether to automatically open the assistant when loaded",
    )
    delay_open: Optional[int] = Field(
        None, description="Delay in milliseconds before auto-opening the assistant"
    )


@router.post("", response_model=AssistantResponse)
async def create_assistant(
    assistant: AssistantCreate, current_user: User = Depends(deps.get_current_user)
) -> AssistantResponse:
    """
    Create a new assistant.
    """
    service = AssistantService()
    return await service.create_assistant(assistant, current_user.id)


@router.get("", response_model=List[AssistantResponse])
async def list_assistants(
    current_user: User = Depends(deps.get_current_user),
) -> List[AssistantResponse]:
    """
    List all assistants for the current user.
    """
    service = AssistantService()
    return await service.get_assistants(current_user.id)


@router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant_id: UUID, current_user: User = Depends(deps.get_current_user)
) -> AssistantResponse:
    """
    Get a specific assistant by ID.
    """
    service = AssistantService()
    assistant = await service.get_assistant(assistant_id, current_user.id)
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )
    return assistant


@router.put("/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(
    assistant_id: UUID,
    assistant_update: AssistantUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> AssistantResponse:
    """
    Update an assistant.
    """
    service = AssistantService()
    updated_assistant = await service.update_assistant(
        assistant_id, assistant_update, current_user.id
    )
    if not updated_assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )
    return updated_assistant


@router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assistant(
    assistant_id: UUID, current_user: User = Depends(deps.get_current_user)
):
    """
    Delete an assistant.
    """
    service = AssistantService()
    deleted = await service.delete_assistant(assistant_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )


@router.get("/{assistant_id}/analytics", response_model=AssistantAnalytics)
async def get_assistant_analytics(
    assistant_id: UUID, current_user: User = Depends(deps.get_current_user)
) -> AssistantAnalytics:
    """
    Get analytics for a specific assistant.
    """
    service = AssistantService()
    # First verify assistant exists and belongs to user
    assistant = await service.get_assistant(assistant_id, current_user.id)
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )
    return await service.get_assistant_analytics(assistant_id, current_user.id)


@router.post("/{assistant_id}/validate")
async def validate_credentials(
    assistant_id: UUID, current_user: User = Depends(deps.get_current_user)
) -> dict:
    """
    Validate OpenAI credentials for an assistant.
    """
    service = AssistantService()
    # First verify assistant exists and belongs to user
    assistant = await service.get_assistant(assistant_id, current_user.id)
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )
    is_valid = await service.validate_openai_credentials(assistant_id, current_user.id)
    return {"is_valid": is_valid}


@router.get("/{assistant_id}/embed")
async def get_embed_code(
    assistant_id: UUID, current_user: User = Depends(deps.get_current_user)
) -> dict:
    """
    Get embed code for an assistant.
    """
    service = AssistantService()
    # First verify assistant exists and belongs to user
    assistant = await service.get_assistant(assistant_id, current_user.id)
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )
    return service.generate_embed_code(assistant_id)


@router.put("/{assistant_id}/embed", response_model=AssistantResponse)
async def update_embed_settings(
    assistant_id: UUID,
    embed_settings: EmbedSettings,
    current_user: User = Depends(deps.get_current_user),
) -> AssistantResponse:
    """
    Update embed settings for an assistant.
    """
    service = AssistantService()
    # First verify assistant exists and belongs to user
    assistant = await service.get_assistant(assistant_id, current_user.id)
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assistant not found"
        )

    # Update the assistant with new embed settings
    updated_assistant = await service.update_assistant(
        assistant_id,
        AssistantUpdate(
            design_settings=DesignSettings(
                layout=LayoutSettings(position=embed_settings.position)
            )
        ),
        current_user.id,
    )

    if not updated_assistant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update embed settings",
        )

    # Update embed-specific settings in a separate table
    await service.update_embed_settings(assistant_id, embed_settings)

    return updated_assistant
