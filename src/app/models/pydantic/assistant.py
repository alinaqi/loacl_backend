from datetime import datetime
from typing import List, Optional

from pydantic import UUID4, BaseModel, Field


class AssistantBase(BaseModel):
    """Base Assistant model."""

    name: str
    description: Optional[str] = None
    openai_assistant_id: str
    model: str = "gpt-4-turbo-preview"
    instructions: Optional[str] = None
    tools: List[str] = []
    metadata: Optional[dict] = None


class AssistantCreate(AssistantBase):
    """Assistant creation model."""

    user_id: UUID4


class AssistantUpdate(AssistantBase):
    """Assistant update model."""

    pass


class AssistantInDB(AssistantBase):
    """Assistant DB model."""

    id: UUID4
    user_id: UUID4
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Assistant(AssistantBase):
    """Assistant response model."""

    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
