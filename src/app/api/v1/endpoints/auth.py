from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_current_user
from app.schemas.user import User, UserCreate
from app.services.auth import auth_service

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user_data: UserCreate) -> User:
    """
    Register a new user.
    """
    return await auth_service.register_user(user_data)

@router.post("/login/access-token")
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the session from Supabase
    session = auth_service.client.auth.get_session()
    return {
        "access_token": session.access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user.
    """
    return current_user 