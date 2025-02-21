import json
from typing import Optional
from uuid import UUID

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from gotrue.errors import AuthApiError
from jose import JWTError, jwt

from app.core.config import Settings, get_settings, get_supabase_client
from app.schemas.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().API_V1_STR}/auth/login/access-token"
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Get the current user from the token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Initialize Supabase client
        client = get_supabase_client()

        # Get user from token
        response = client.auth.get_user(token)
        print(f"User response: {response}")

        if not response or not response.user:
            raise credentials_exception

        user_data = response.user
        return User(
            id=UUID(user_data.id),
            email=user_data.email,
            is_active=True,
            is_superuser=False,
            full_name=(
                user_data.user_metadata.get("full_name")
                if user_data.user_metadata
                else None
            ),
        )
    except AuthApiError as e:
        print(f"Auth API error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise credentials_exception


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not token:
        return None
    return await get_current_user(token)
