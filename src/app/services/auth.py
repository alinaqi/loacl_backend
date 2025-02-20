"""
Authentication service module.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import jwt
from supabase import Client

from app.core.config import get_settings
from app.core.logger import get_logger
from app.models.auth import (
    GuestSessionRequest,
    GuestSessionResponse,
    SessionConversionRequest,
    TokenResponse,
)

logger = get_logger(__name__)


class AuthService:
    """Service for handling authentication."""

    def __init__(self, client: Client):
        """Initialize service with Supabase client."""
        self.client = client
        self.settings = get_settings()

    async def authenticate(self, client_id: str, client_secret: str) -> TokenResponse:
        """
        Authenticate a client and return a token.

        Args:
            client_id: Client ID
            client_secret: Client secret

        Returns:
            TokenResponse: Authentication token response
        """
        # Validate credentials
        response = (
            await self.client.table("clients")
            .select("*")
            .eq("client_id", client_id)
            .execute()
        )
        if not response.data:
            raise ValueError("Invalid client credentials")

        client = response.data[0]
        if client["client_secret"] != client_secret:
            raise ValueError("Invalid client credentials")

        # Generate token
        token = self._generate_token(client_id)
        return TokenResponse(access_token=token)

    async def create_guest_session(
        self, request: GuestSessionRequest
    ) -> GuestSessionResponse:
        """
        Create a temporary guest session.

        Args:
            request: Guest session request

        Returns:
            GuestSessionResponse: Guest session details
        """
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)

        # Create session record
        await self.client.table("guest_sessions").insert(
            {
                "id": session_id,
                "metadata": request.metadata,
                "expires_at": expires_at.isoformat(),
            }
        ).execute()

        return GuestSessionResponse(
            session_id=session_id,
            expires_at=expires_at,
        )

    async def convert_guest_session(
        self, request: SessionConversionRequest
    ) -> TokenResponse:
        """
        Convert a guest session to an authenticated session.

        Args:
            request: Session conversion request

        Returns:
            TokenResponse: New authentication token
        """
        # Validate session exists
        response = (
            await self.client.table("guest_sessions")
            .select("*")
            .eq("id", request.session_id)
            .execute()
        )
        if not response.data:
            raise ValueError("Invalid session ID")

        session = response.data[0]
        if datetime.fromisoformat(session["expires_at"]) < datetime.utcnow():
            raise ValueError("Session has expired")

        # Generate token
        token = self._generate_token(request.client_id)

        # Update session data
        await self.client.table("guest_sessions").update(
            {
                "converted_at": datetime.utcnow().isoformat(),
                "client_id": request.client_id,
            }
        ).eq("id", request.session_id).execute()

        return TokenResponse(access_token=token)

    async def delete_guest_session(self, session_id: str) -> None:
        """
        Delete a guest session.

        Args:
            session_id: Session ID to delete
        """
        response = (
            await self.client.table("guest_sessions")
            .delete()
            .eq("id", session_id)
            .execute()
        )
        if not response.data:
            raise ValueError("Session not found")

    def _generate_token(
        self, client_id: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Generate a JWT token.

        Args:
            client_id: Client ID to include in token
            expires_delta: Optional expiration delta

        Returns:
            str: JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(days=1)

        expires_at = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": client_id,
            "exp": expires_at,
        }
        return jwt.encode(to_encode, self.settings.SECRET_KEY, algorithm="HS256")
