"""
Thread models module.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import BaseModelTimestamps


class MessageRole(str, Enum):
    """Message role enumeration."""
    
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message status enumeration."""
    
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_ACTION = "requires_action"


class ThreadBase(BaseModel):
    """Base thread model."""
    
    title: Optional[str] = Field(None, description="Title of the thread")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class ThreadCreate(ThreadBase):
    """Thread creation model."""
    
    assistant_id: UUID = Field(..., description="ID of the assistant to use")


class ThreadUpdate(ThreadBase):
    """Thread update model."""
    
    title: Optional[str] = None
    metadata: Optional[Dict] = None
    is_active: Optional[bool] = None


class Thread(ThreadBase, BaseModelTimestamps):
    """Thread model with ID and timestamps."""
    
    id: UUID = Field(..., description="Unique identifier")
    assistant_id: UUID = Field(..., description="ID of the assistant")
    openai_thread_id: str = Field(..., description="OpenAI thread ID")
    is_active: bool = Field(default=True, description="Whether the thread is active")


class MessageBase(BaseModel):
    """Base message model."""
    
    content: str = Field(..., description="Message content")
    role: MessageRole = Field(default=MessageRole.USER, description="Role of the message sender")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class MessageCreate(MessageBase):
    """Message creation model."""
    pass


class Message(MessageBase, BaseModelTimestamps):
    """Message model with ID and timestamps."""
    
    id: UUID = Field(..., description="Unique identifier")
    thread_id: UUID = Field(..., description="ID of the thread")
    openai_message_id: str = Field(..., description="OpenAI message ID")
    status: MessageStatus = Field(default=MessageStatus.QUEUED, description="Status of the message")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    error: Optional[str] = Field(None, description="Error message if failed") 