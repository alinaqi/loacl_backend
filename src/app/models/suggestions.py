"""
Suggestions models module.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FollowUpSuggestion(BaseModel):
    """Follow-up suggestion model."""

    id: Optional[UUID] = None
    thread_id: UUID
    message_id: Optional[UUID] = None
    suggestion: str = Field(..., description="The suggested follow-up question")
    created_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class SuggestionsResponse(BaseModel):
    """Response model for suggestions."""

    suggestions: List[str] = Field(..., description="List of follow-up suggestions")
