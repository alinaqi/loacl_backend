"""
Assistant configuration endpoints.
"""

from fastapi import APIRouter, HTTPException

from app.models.assistant import AssistantConfiguration
from app.services.dependencies import get_assistant_service

router = APIRouter(prefix="/assistant", tags=["Assistant"])

# Get singleton service instance
assistant_service = get_assistant_service()


@router.get("/configuration")
async def get_configuration():
    """
    Get current assistant configuration.

    Returns:
        dict: Current configuration with status

    Raises:
        HTTPException: If configuration retrieval fails
    """
    try:
        # Get current assistant configuration
        config = await assistant_service.get_configuration()
        return {"status": "success", "data": config}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get configuration: {str(e)}"
        )
