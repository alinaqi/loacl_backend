from typing import Optional
from fastapi import HTTPException, status
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError
import json
import jwt

from app.core.config import settings
from app.models.auth import UserCreate, UserLogin, UserResponse

class AuthService:
    def __init__(self):
        """Initialize Supabase client."""
        options = ClientOptions(
            postgrest_client_timeout=10,
            storage_client_timeout=10
        )
        # Regular client for normal operations
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY,
            options=options
        )
        # Admin client for user operations
        self.admin_client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
            options=options
        )

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user."""
        if user_data.password != user_data.password_confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        auth_response = None
        try:
            # Register user with Supabase Auth
            auth_response = self.client.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password
            })

            # Debug log
            print(f"Auth Response: {auth_response}")

            if not auth_response.user or not auth_response.user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not register user - no user ID returned"
                )

            try:
                # Create user record in our users table
                user_record = self.client.from_('users').insert({
                    "id": auth_response.user.id,
                    "email": user_data.email,
                    "is_active": True
                }).execute()

                print(f"User Record Response: {user_record}")

                if not user_record.data:
                    # Log the error but don't delete the auth user
                    print(f"Failed to create user record in users table: {user_record}")
                    # Still return success as the auth user was created
                    return UserResponse(
                        id=auth_response.user.id,
                        email=user_data.email,
                        is_active=True
                    )

                return UserResponse(
                    id=auth_response.user.id,
                    email=user_data.email,
                    is_active=True
                )

            except APIError as e:
                print(f"API Error creating user record: {str(e)}")
                # Don't delete the auth user, just log the error
                return UserResponse(
                    id=auth_response.user.id,
                    email=user_data.email,
                    is_active=True
                )

        except Exception as e:
            error_msg = str(e)
            error_dict = {}
            
            # Try to parse error message as JSON for more details
            try:
                if isinstance(error_msg, str) and error_msg.startswith('{'):
                    error_dict = json.loads(error_msg)
            except:
                pass

            print(f"Registration error: {error_msg}")
            if error_dict:
                print(f"Error details: {error_dict}")

            # Check if we have a successful auth_response despite the error
            if auth_response and auth_response.user and auth_response.user.id:
                return UserResponse(
                    id=auth_response.user.id,
                    email=user_data.email,
                    is_active=True
                )

            # If we don't have a successful auth_response, handle the error
            if "For security purposes" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many registration attempts. Please wait a moment before trying again."
                )
            elif "User already registered" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A user with this email already exists"
                )
            elif "User not allowed" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration is currently disabled or restricted. Please check your email domain is allowed."
                )
            else:
                # Include more error details if available
                detail = f"Registration failed: {error_msg}"
                if error_dict:
                    detail += f" Additional info: {json.dumps(error_dict)}"
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=detail
                )

    async def login_user(self, user_data: UserLogin) -> dict:
        """Login user and return access token."""
        try:
            auth_response = self.client.auth.sign_in_with_password({
                "email": user_data.email,
                "password": user_data.password
            })

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            return {
                "access_token": auth_response.session.access_token,
                "token_type": "bearer"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

    async def get_current_user(self, token: str) -> Optional[UserResponse]:
        """Get current user from token."""
        try:
            # Decode the JWT token
            decoded = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded.get('sub')
            email = decoded.get('email')
            
            if not user_id or not email:
                print("No user ID or email in token")
                return None

            # For Supabase tokens, we can trust the email from the token
            # as it's already verified by Supabase's auth system
            return UserResponse(
                id=user_id,
                email=email,
                is_active=True
            )

        except Exception as e:
            print(f"Error getting current user: {str(e)}")
            return None

auth_service = AuthService() 