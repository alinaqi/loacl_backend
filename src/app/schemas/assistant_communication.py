from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a new message in a thread"""

    content: str = Field(..., description="The content of the message")
    file_ids: Optional[List[str]] = Field(
        default=None, description="List of file IDs to attach to the message"
    )


class Message(BaseModel):
    """Schema for a message in a thread"""

    id: str
    thread_id: str
    role: str
    content: List[Dict[str, Any]]
    file_ids: Optional[List[str]] = None
    created_at: int


class ThreadCreate(BaseModel):
    """Schema for creating a new thread"""

    messages: Optional[List[MessageCreate]] = Field(
        default=None, description="Initial messages to add to the thread"
    )


class Thread(BaseModel):
    """Schema for a thread"""

    id: str
    object: str = Field(default="thread")
    created_at: int
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"  # Allow extra fields from OpenAI response


class RunCreate(BaseModel):
    """Schema for creating a new run"""

    assistant_id: str = Field(..., description="Assistant ID to use for the run")
    instructions: Optional[str] = Field(
        default=None, description="Override instructions for this run"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Tools to use for this run"
    )


class Run(BaseModel):
    """Schema for a run"""

    id: str
    thread_id: str
    assistant_id: str
    status: str
    created_at: int
    started_at: Optional[int] = None
    expires_at: Optional[int] = None
    completed_at: Optional[int] = None
    last_error: Optional[Dict[str, Any]] = None
    required_action: Optional[Dict[str, Any]] = None


class ToolOutput(BaseModel):
    """Schema for tool output"""

    tool_call_id: str = Field(..., description="ID of the tool call")
    output: str = Field(..., description="Output from the tool")


class ChatSession(BaseModel):
    """Schema for a chat session"""

    id: UUID
    assistant_id: UUID
    fingerprint: str
    created_at: str
    last_active_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    """Schema for a chat message"""

    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: str
    tokens_used: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
