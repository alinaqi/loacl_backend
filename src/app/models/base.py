from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TimestampModel(BaseModel):
    """Base model with timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ResponseModel(BaseModel):
    """Standard response model."""
    status: str
    message: str
    data: Optional[dict] = None 