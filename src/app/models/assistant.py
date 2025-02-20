"""
Assistant models module.
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import BaseModelTimestamps


class AssistantBase(BaseModel):
    """Base assistant model."""
    
    name: str = Field(..., description="Name of the assistant")
    description: Optional[str] = Field(None, description="Description of the assistant")
    instructions: str = Field(..., description="Instructions for the assistant")
    model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model to use")
    tools: List[Dict] = Field(default_factory=list, description="Tools available to the assistant")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class AssistantCreate(AssistantBase):
    """Assistant creation model."""
    pass


class AssistantUpdate(AssistantBase):
    """Assistant update model."""
    
    name: Optional[str] = None
    instructions: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None


class Assistant(AssistantBase, BaseModelTimestamps):
    """Assistant model with ID and timestamps."""
    
    id: UUID = Field(..., description="Unique identifier")
    openai_assistant_id: str = Field(..., description="OpenAI assistant ID")
    is_active: bool = Field(default=True, description="Whether the assistant is active") 