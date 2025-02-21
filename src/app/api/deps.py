from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.core.config import get_settings, Settings
from app.schemas.user import User
from app.core.config import get_supabase_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().API_V1_STR}/auth/login/access-token")

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
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
        
        # Set the session with the provided token
        client.auth.set_session(token)
        
        # Get the current session
        session = client.auth.get_session()
        if not session or not session.user:
            raise credentials_exception

        user = session.user
        return User(
            id=UUID(user.id),
            email=user.email,
            is_active=True,
            is_superuser=False,
            full_name=user.user_metadata.get('full_name') if user.user_metadata else None
        )
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise credentials_exception

async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not token:
        return None
    return await get_current_user(token) 