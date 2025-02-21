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
    try:
        print(f"Attempting login for user: {form_data.username}")
        # Sign in with Supabase
        auth_response = auth_service.client.auth.sign_in_with_password(
            {"email": form_data.username, "password": form_data.password}
        )

        print(f"Auth response user: {auth_response.user}")
        print(f"Auth response session: {auth_response.session}")

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Return the session data
        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
        }
    except Exception as e:
        print(f"Login error details: {str(e)}")
        if hasattr(e, "message"):
            error_message = e.message
        else:
            error_message = str(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {error_message}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user.
    """
    return current_user
