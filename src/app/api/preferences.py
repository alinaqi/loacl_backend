"""
User preferences endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from app.core.auth import get_current_user
from app.models.preferences import UserPreferences, UserPreferencesUpdate
from app.services.preferences import UserPreferencesService

router = APIRouter(prefix="/preferences", tags=["Preferences"])
security = HTTPBearer()


@router.get("", response_model=UserPreferences)
async def get_preferences(
    current_user: UUID = Depends(get_current_user),
    preferences_service: UserPreferencesService = Depends(),
) -> UserPreferences:
    """
    Get user preferences.

    Args:
        current_user: Current authenticated user ID
        preferences_service: Injected preferences service

    Returns:
        UserPreferences: User preferences

    Raises:
        HTTPException: If preferences retrieval fails
    """
    try:
        return await preferences_service.get_preferences(current_user)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user preferences: {str(e)}"
        )


@router.patch("", response_model=UserPreferences)
async def update_preferences(
    data: UserPreferencesUpdate,
    current_user: UUID = Depends(get_current_user),
    preferences_service: UserPreferencesService = Depends(),
) -> UserPreferences:
    """
    Update user preferences.

    Args:
        data: Update data
        current_user: Current authenticated user ID
        preferences_service: Injected preferences service

    Returns:
        UserPreferences: Updated user preferences

    Raises:
        HTTPException: If preferences update fails
    """
    try:
        return await preferences_service.update_preferences(
            user_id=current_user, data=data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update user preferences: {str(e)}"
        )
