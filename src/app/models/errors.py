"""
Error models module.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.base import BaseResponse


class ErrorDetail(BaseModel):
    """Detailed error information."""

    loc: List[str] = Field(..., description="Location of the error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ErrorResponse(BaseResponse):
    """Standard error response model."""

    status: str = "error"
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(
        None, description="Detailed error information"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional error metadata"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "error",
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": [
                    {
                        "loc": ["body", "name"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ],
            }
        }
    }


class HTTPError(Exception):
    """Base HTTP error exception."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details
        self.metadata = metadata
        super().__init__(message)

    def to_response(self) -> ErrorResponse:
        """Convert exception to ErrorResponse model."""
        return ErrorResponse(
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            metadata=self.metadata,
        )
