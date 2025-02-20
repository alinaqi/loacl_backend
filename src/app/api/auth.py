from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.assistant import AssistantInitResponse
from app.services.assistant import AssistantService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class AssistantInitRequest(BaseModel):
    """Request model for assistant initialization"""

    assistant_id: str
    configuration: Optional[dict] = None


@router.post("/initialize", response_model=AssistantInitResponse)
async def initialize_assistant(
    request: AssistantInitRequest, assistant_service: AssistantService = Depends()
) -> AssistantInitResponse:
    """
    Initialize an assistant session

    Args:
        request: Assistant initialization parameters
        assistant_service: Injected assistant service

    Returns:
        AssistantInitResponse: Initialized assistant details

    Raises:
        HTTPException: If assistant initialization fails
    """
    try:
        return await assistant_service.initialize(
            assistant_id=request.assistant_id, configuration=request.configuration
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to initialize assistant: {str(e)}"
        )
