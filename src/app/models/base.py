"""
Base models module.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseModelTimestamps(BaseModel):
    """Base model with timestamps."""
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            UUID: lambda uuid: str(uuid),
        },
    )


class BaseResponse(BaseModel):
    """Base response model."""
    
    status: str = "success"
    message: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
            }
        }
    ) 