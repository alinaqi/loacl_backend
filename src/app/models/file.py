"""
File models module.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import BaseModelTimestamps


class FileStatus(str, Enum):
    """File status enumeration."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class FileBase(BaseModel):
    """Base file model."""
    
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File MIME type")
    size: int = Field(..., description="File size in bytes")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")


class FileCreate(FileBase):
    """File creation model."""
    pass


class FileUpdate(FileBase):
    """File update model."""
    
    filename: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    metadata: Optional[Dict] = None


class File(FileBase, BaseModelTimestamps):
    """File model with ID and timestamps."""
    
    id: UUID = Field(..., description="Unique identifier")
    openai_file_id: Optional[str] = Field(None, description="OpenAI file ID")
    storage_path: str = Field(..., description="Path in storage")
    status: FileStatus = Field(default=FileStatus.PENDING, description="Status of the file")
    error: Optional[str] = Field(None, description="Error message if failed")


class FileResponse(BaseModel):
    """File response model."""
    
    id: UUID = Field(..., description="File ID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="File MIME type")
    size: int = Field(..., description="File size in bytes")
    status: FileStatus = Field(..., description="Status of the file")
    created_at: datetime = Field(..., description="Creation timestamp") 