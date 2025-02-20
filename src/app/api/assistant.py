"""
Assistant configuration endpoints.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.assistant import AssistantConfiguration
from app.services.assistant import AssistantService

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.get("/configuration", response_model=AssistantConfiguration)
async def get_configuration(
    assistant_service: AssistantService = Depends(),
) -> AssistantConfiguration:
    """
    Get current assistant configuration.

    Args:
        assistant_service: Injected assistant service

    Returns:
        AssistantConfiguration: Current assistant configuration

    Raises:
        HTTPException: If configuration retrieval fails
    """
    try:
        # Get current assistant configuration
        config = await assistant_service.get_configuration()
        return AssistantConfiguration(**config)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get assistant configuration: {str(e)}"
        )
