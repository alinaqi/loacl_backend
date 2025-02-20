"""
Authentication service module.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import Depends
from jose import jwt
from supabase import Client

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.core.supabase import get_supabase_client
from app.models.auth import (
    GuestSessionRequest,
    GuestSessionResponse,
    SessionConversionRequest,
    TokenResponse,
)
from app.repositories.session import SessionRepository
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        client: Client = Depends(get_supabase_client),
    ):
        """
        Initialize service.

        Args:
            settings: Application settings
            client: Supabase client
        """
        self.settings = settings
        self.user_repo = UserRepository(client)
        self.session_repo = SessionRepository(client)

    async def authenticate(self, client_id: str, client_secret: str) -> TokenResponse:
        """
        Authenticate user with client credentials.

        Args:
            client_id: Client ID
            client_secret: Client secret

        Returns:
            TokenResponse: Authentication token response

        Raises:
            ValueError: If authentication fails
        """
        try:
            # Validate client credentials
            user = await self.user_repo.get_by_client_credentials(
                client_id=client_id, client_secret=client_secret
            )
            if not user:
                raise ValueError("Invalid client credentials")

            # Generate JWT token
            expires_delta = timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            expires_at = datetime.utcnow() + expires_delta

            to_encode = {"sub": str(user.id), "exp": expires_at}

            access_token = jwt.encode(
                to_encode,
                self.settings.JWT_SECRET_KEY,
                algorithm=self.settings.JWT_ALGORITHM,
            )

            return TokenResponse(access_token=access_token, expires_at=expires_at)

        except Exception as e:
            logger.error("Authentication failed", error=str(e))
            raise

    async def create_guest_session(
        self, request: GuestSessionRequest
    ) -> GuestSessionResponse:
        """
        Create a guest session.

        Args:
            request: Guest session request

        Returns:
            GuestSessionResponse: Guest session details

        Raises:
            ValueError: If session creation fails
        """
        try:
            # Create guest session
            session = await self.session_repo.create_guest_session(request)
            if not session:
                raise ValueError("Failed to create guest session")

            # Generate temporary JWT token
            expires_at = datetime.fromisoformat(session["expires_at"])
            to_encode = {
                "sub": str(session["id"]),
                "exp": expires_at,
                "type": "guest",
            }

            access_token = jwt.encode(
                to_encode,
                self.settings.JWT_SECRET_KEY,
                algorithm=self.settings.JWT_ALGORITHM,
            )

            return GuestSessionResponse(
                session_id=session["id"],
                access_token=access_token,
            )

        except Exception as e:
            logger.error("Failed to create guest session", error=str(e))
            raise

    async def convert_guest_session(
        self, request: SessionConversionRequest
    ) -> TokenResponse:
        """
        Convert a guest session to an authenticated session.

        Args:
            request: Session conversion request containing session ID and user credentials

        Returns:
            TokenResponse: New authentication token for the converted session

        Raises:
            ValueError: If session not found or invalid credentials
            HTTPException: If session conversion fails
        """
        try:
            # Validate user credentials
            user = await self.user_repo.get_by_client_credentials(
                client_id=request.client_id, client_secret=request.client_secret
            )
            if not user:
                raise ValueError("Invalid client credentials")

            # Get and validate guest session
            session = await self.session_repo.get_by_id(request.session_id)
            if not session:
                raise ValueError("Session not found")
            if session.session_type != "guest":
                raise ValueError("Only guest sessions can be converted")
            if session.status != "active":
                raise ValueError("Session is not active")

            # Update session with user ID and type
            updated_session = await self.session_repo.update(
                session.id,
                {
                    "session_type": "authenticated",
                    "user_id": user.id,
                    "expires_at": None,  # Authenticated sessions don't expire
                },
            )
            if not updated_session:
                raise ValueError("Failed to update session")

            # Generate new JWT token
            expires_delta = timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            expires_at = datetime.utcnow() + expires_delta

            to_encode = {"sub": str(user.id), "exp": expires_at}
            access_token = jwt.encode(
                to_encode,
                self.settings.JWT_SECRET_KEY,
                algorithm=self.settings.JWT_ALGORITHM,
            )

            return TokenResponse(access_token=access_token, expires_at=expires_at)

        except Exception as e:
            logger.error("Failed to convert guest session", error=str(e))
            raise

    async def delete_guest_session(self, session_id: UUID) -> None:
        """
        Delete a guest session and all associated data.

        Args:
            session_id: The ID of the guest session to delete

        Raises:
            ValueError: If session not found or is not a guest session
            Exception: If deletion fails
        """
        try:
            # Get and validate guest session
            session = await self.session_repo.get_by_id(session_id)
            if not session:
                raise ValueError("Session not found")
            if session.session_type != "guest":
                raise ValueError(
                    "Only guest sessions can be deleted through this endpoint"
                )

            # Delete the session and all associated data
            await self.session_repo.delete(session_id)

        except Exception as e:
            logger.error("Failed to delete guest session", error=str(e))
            raise
