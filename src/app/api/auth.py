from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.assistant import AssistantInitResponse
from app.models.auth import (
    GuestSessionRequest,
    GuestSessionResponse,
    SessionConversionRequest,
    TokenRequest,
    TokenResponse,
)
from app.services.assistant import AssistantService
from app.services.auth import AuthService

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


@router.post("/token", response_model=TokenResponse)
async def get_auth_token(
    request: TokenRequest, auth_service: AuthService = Depends()
) -> TokenResponse:
    """
    Get authentication token for persistent user sessions.

    Args:
        request: Token request with client credentials
        auth_service: Injected auth service

    Returns:
        TokenResponse: Authentication token response

    Raises:
        HTTPException: If authentication fails
    """
    try:
        return await auth_service.authenticate(
            client_id=request.client_id, client_secret=request.client_secret
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


@router.post("/guest", response_model=GuestSessionResponse)
async def create_guest_session(
    request: GuestSessionRequest, auth_service: AuthService = Depends()
) -> GuestSessionResponse:
    """
    Create a temporary guest session.

    Args:
        request: Guest session request parameters
        auth_service: Injected auth service

    Returns:
        GuestSessionResponse: Guest session details

    Raises:
        HTTPException: If session creation fails
    """
    try:
        return await auth_service.create_guest_session(request)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create guest session: {str(e)}"
        )


@router.post("/convert-session", response_model=TokenResponse)
async def convert_session(
    request: SessionConversionRequest,
    auth_service: AuthService = Depends(),
) -> dict:
    """
    Convert a guest session to an authenticated session.

    Args:
        request: Session conversion request
        auth_service: Authentication service

    Returns:
        dict: New authentication token response

    Raises:
        HTTPException: If session conversion fails
    """
    try:
        response = await auth_service.convert_guest_session(request)
        return {"status": "success", "data": response.dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to convert session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to convert session")


@router.delete("/guest/sessions/{session_id}", status_code=204)
async def delete_guest_session(
    session_id: UUID,
    auth_service: AuthService = Depends(),
) -> None:
    """
    Delete a guest session and all associated data.

    Args:
        session_id: The ID of the guest session to delete
        auth_service: Injected auth service

    Raises:
        HTTPException: If session deletion fails or session is not found
    """
    try:
        await auth_service.delete_guest_session(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete guest session", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete guest session")
