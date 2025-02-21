from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models.auth import UserResponse
from app.services.auth import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login/access-token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """Get current authenticated user."""
    try:
        user = await auth_service.get_current_user(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[UserResponse]:
    """Get current user if authenticated, otherwise return None."""
    if not token:
        return None
    return await auth_service.get_current_user(token) 