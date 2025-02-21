import json
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from jose import jwt
from postgrest.exceptions import APIError
from pydantic import EmailStr
from supabase.lib.client_options import ClientOptions

from app.core.config import get_settings, get_supabase_client
from app.schemas.user import User, UserCreate
from supabase import Client, create_client


class AuthService:
    def __init__(self):
        """Initialize Supabase client."""
        self.settings = get_settings()
        self.client = get_supabase_client()

    async def authenticate_user(self, email: EmailStr, password: str) -> Optional[User]:
        try:
            print(f"Attempting to authenticate user: {email}")
            # Use Supabase auth
            auth_response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            print(f"Auth response received: {auth_response}")

            if not auth_response.user:
                return None

            # Convert Supabase user to our User model
            return User(
                id=UUID(auth_response.user.id),
                email=auth_response.user.email,
                is_active=True,
                is_superuser=False,
                full_name=(
                    auth_response.user.user_metadata.get("full_name")
                    if auth_response.user.user_metadata
                    else None
                ),
            )
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None

    async def register_user(self, user_data: UserCreate) -> User:
        try:
            # Use Supabase auth.sign_up with user metadata
            result = self.client.auth.sign_up(
                {
                    "email": user_data.email,
                    "password": user_data.password,
                    "options": {"data": {"full_name": user_data.full_name}},
                }
            )

            if not result.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not register user",
                )

            return User(
                id=UUID(result.user.id),
                email=result.user.email,
                is_active=True,
                is_superuser=False,
                full_name=user_data.full_name,
            )
        except Exception as e:
            print(f"Registration error: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_current_user(self, token: str) -> Optional[User]:
        try:
            # Get the current session
            session = self.client.auth.get_session()
            if not session:
                return None

            user = session.user
            if not user:
                return None

            return User(
                id=UUID(user.id),
                email=user.email,
                is_active=True,
                is_superuser=False,
                full_name=(
                    user.user_metadata.get("full_name") if user.user_metadata else None
                ),
            )
        except Exception as e:
            print(f"Get current user error: {str(e)}")
            return None


# Create a global instance of AuthService
auth_service = AuthService()
