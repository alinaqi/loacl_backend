"""
Core dependencies module.

This module provides common dependencies used across the application,
particularly for authentication and authorization.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core.logger import get_logger
from app.models.auth import TokenData
from app.services.auth import AuthService

logger = get_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthService = Depends(),
) -> TokenData:
    """
    Get the current authenticated user from the JWT token.

    Args:
        token: JWT token from authorization header
        auth_service: Authentication service instance

    Returns:
        TokenData: Current user data

    Raises:
        HTTPException: If authentication fails
    """
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        settings = get_settings()

        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Extract user information
        user_id: Optional[UUID] = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
            )

        # Create token data
        token_data = TokenData(user_id=UUID(user_id))

        return token_data

    except JWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
        )
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
        )


async def get_optional_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    auth_service: AuthService = Depends(),
) -> Optional[TokenData]:
    """
    Get the current user if authenticated, otherwise return None.

    Args:
        token: Optional JWT token from authorization header
        auth_service: Authentication service instance

    Returns:
        Optional[TokenData]: Current user data or None if not authenticated
    """
    if not token:
        return None

    try:
        return await get_current_user(token, auth_service)
    except HTTPException:
        return None
