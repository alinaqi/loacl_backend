"""
Response models for handling OpenAI responses.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import BaseResponse


class ResponseMode(str, Enum):
    """Response mode enumeration."""

    NORMAL = "normal"
    STREAMING = "streaming"


class ResponseChunk(BaseModel):
    """Model for a streaming response chunk."""

    thread_id: UUID = Field(..., description="Thread ID")
    message_id: UUID = Field(..., description="Message ID")
    content: str = Field(..., description="Chunk content")
    is_complete: bool = Field(
        default=False, description="Whether this is the final chunk"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NormalResponse(BaseResponse):
    """Model for a normal (non-streaming) response."""

    thread_id: UUID = Field(..., description="Thread ID")
    message_id: UUID = Field(..., description="Message ID")
    content: str = Field(..., description="Complete response content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ResponseConfig(BaseModel):
    """Configuration for response handling."""

    mode: ResponseMode = Field(default=ResponseMode.NORMAL, description="Response mode")
    chunk_size: Optional[int] = Field(None, description="Size of chunks for streaming")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(
        None, description="Temperature for response generation"
    )
    stream_callback: Optional[str] = Field(
        None, description="Callback URL for streaming updates"
    )
