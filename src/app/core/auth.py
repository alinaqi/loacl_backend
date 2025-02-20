"""
Authentication module.
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.logger import get_logger
from app.models.user import User

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[User]:
    """
    Get the current authenticated user.

    Args:
        token: JWT token from request

    Returns:
        Optional[User]: Current user if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # For now, return a mock user for development
        return User(
            id=UUID("00000000-0000-0000-0000-000000000000"),
            email="dev@example.com",
            is_active=True,
            is_superuser=False,
        )
    except Exception as e:
        logger.error("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
