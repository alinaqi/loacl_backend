from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.assistant import AssistantInitResponse
from app.models.auth import (
    GuestSessionRequest,
    GuestSessionResponse,
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
