from fastapi import APIRouter

api_router = APIRouter()

# Import and include other routers here
# Example:
# from .endpoints import users, chat, assistants
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# api_router.include_router(assistants.router, prefix="/assistants", tags=["assistants"]) 