"""
Authentication service module.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends
from jose import jwt

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
from app.models.auth import TokenResponse
from app.repositories.user import UserRepository

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(
        self,
        settings: Settings = Depends(get_settings),
        user_repo: UserRepository = Depends(),
    ):
        """
        Initialize service.

        Args:
            settings: Application settings
            user_repo: User repository
        """
        self.settings = settings
        self.user_repo = user_repo

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
