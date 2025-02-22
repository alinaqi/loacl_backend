import json
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

import jwt as pyjwt
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from gotrue.errors import AuthApiError
from jose import JWTError, jwt
from supabase import create_client, ClientOptions

from app.core.config import Settings, get_settings, get_supabase_client
from app.schemas.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().API_V1_STR}/auth/login/access-token",
    auto_error=False
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_user_from_api_key(api_key: str) -> Optional[User]:
    """
    Get user from API key.
    """
    try:
        settings = get_settings()
        
        # Create service role JWT
        service_role_jwt = jwt.encode(
            {
                "role": "service_role",
                "iss": "supabase",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(days=1),
                "sub": "service_role",  # Important for service role auth
            },
            settings.SUPABASE_JWT_SECRET,
            algorithm="HS256",
        )

        # Use service role key with proper JWT
        options = ClientOptions(
            headers={
                "apiKey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {service_role_jwt}",
            }
        )

        # Initialize Supabase client with service role
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
            options=options
        )

        # Query the API key
        result = client.table("lacl_api_keys").select("user_id").eq("key", api_key).execute()

        if not result.data:
            return None

        # Get user details
        user_id = result.data[0]["user_id"]
        user_result = client.auth.admin.get_user_by_id(user_id)

        if not user_result or not user_result.user:
            return None

        user_data = user_result.user
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
    except Exception as e:
        print(f"API key authentication error: {str(e)}")
        return None


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(api_key_header)
) -> User:
    """
    Get the current user from either the token or API key.
    At least one authentication method must be provided.
    
    Args:
        token: Optional Bearer token
        api_key: Optional API key
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If no valid authentication is provided or if authentication fails
    """
    if not token and not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide either a Bearer token or API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try API key first if provided
    if api_key:
        user = await get_user_from_api_key(api_key)
        if user:
            return user
        # If API key was provided but invalid, return specific error
        if not token:  # Only raise if we don't have a token to try next
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

    # Try token if provided
    if token:
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Bearer token",
            )
        except Exception as e:
            print(f"Auth error: {str(e)}")
            raise credentials_exception

    # If we get here, neither authentication method worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed. Both API key and Bearer token were invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not token and not api_key:
        return None
    try:
        return await get_current_user(token, api_key)
    except HTTPException:
        return None
