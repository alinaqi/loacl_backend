from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID

class MessageCreate(BaseModel):
    """Schema for creating a new message in a thread"""
    content: str = Field(..., description="The content of the message")
    file_ids: Optional[List[str]] = Field(default=None, description="List of file IDs to attach to the message")

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
    messages: Optional[List[MessageCreate]] = Field(default=None, description="Initial messages to add to the thread")

class Thread(BaseModel):
    """Schema for a thread"""
    id: str
    created_at: int
    metadata: Optional[Dict[str, Any]] = None

class RunCreate(BaseModel):
    """Schema for creating a new run"""
    assistant_id: str = Field(..., description="The ID of the assistant to use for this run")
    instructions: Optional[str] = Field(default=None, description="Override the assistant's instructions for this run")
    tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="Override the assistant's tools for this run")

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
    """Schema for submitting tool outputs"""
    tool_call_id: str = Field(..., description="The ID of the tool call to respond to")
    output: str = Field(..., description="The output of the tool call") 