"""API key management endpoints."""

import secrets
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.core.config import get_supabase_client
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyUpdate
from app.schemas.user import User

router = APIRouter()


@router.post("", response_model=APIKeyResponse)
async def create_api_key(
    api_key: APIKeyCreate,
    current_user: User = Depends(deps.get_current_user),
) -> APIKeyResponse:
    """Create a new API key.

    Args:
        api_key: API key creation data
        current_user: Current authenticated user

    Returns:
        Created API key
    """
    # Generate a secure random API key
    key_value = f"loacl_{secrets.token_urlsafe(32)}"

    # Create API key in database
    supabase = get_supabase_client()
    result = (
        supabase.table("lacl_api_keys")
        .insert(
            {
                "user_id": str(current_user.id),
                "name": api_key.name,
                "key": key_value,
            }
        )
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )

    return APIKeyResponse(**result.data[0])


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(deps.get_current_user),
) -> List[APIKeyResponse]:
    """List all API keys for the current user.

    Args:
        current_user: Current authenticated user

    Returns:
        List of API keys
    """
    supabase = get_supabase_client()
    result = (
        supabase.table("lacl_api_keys")
        .select("*")
        .eq("user_id", str(current_user.id))
        .execute()
    )
    return [APIKeyResponse(**row) for row in result.data]


@router.get("/{api_key_id}", response_model=APIKeyResponse)
async def get_api_key(
    api_key_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> APIKeyResponse:
    """Get a specific API key.

    Args:
        api_key_id: ID of the API key to retrieve
        current_user: Current authenticated user

    Returns:
        API key details

    Raises:
        HTTPException: If API key not found
    """
    supabase = get_supabase_client()
    result = (
        supabase.table("lacl_api_keys")
        .select("*")
        .match({"id": str(api_key_id), "user_id": str(current_user.id)})
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return APIKeyResponse(**result.data[0])


@router.patch("/{api_key_id}", response_model=APIKeyResponse)
async def update_api_key(
    api_key_id: UUID,
    api_key_update: APIKeyUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> APIKeyResponse:
    """Update an API key.

    Args:
        api_key_id: ID of the API key to update
        api_key_update: Update data
        current_user: Current authenticated user

    Returns:
        Updated API key

    Raises:
        HTTPException: If API key not found
    """
    update_data = api_key_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    supabase = get_supabase_client()
    result = (
        supabase.table("lacl_api_keys")
        .update(update_data)
        .match({"id": str(api_key_id), "user_id": str(current_user.id)})
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return APIKeyResponse(**result.data[0])


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> None:
    """Delete an API key.

    Args:
        api_key_id: ID of the API key to delete
        current_user: Current authenticated user

    Raises:
        HTTPException: If API key not found
    """
    supabase = get_supabase_client()
    result = (
        supabase.table("lacl_api_keys")
        .delete()
        .match({"id": str(api_key_id), "user_id": str(current_user.id)})
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
