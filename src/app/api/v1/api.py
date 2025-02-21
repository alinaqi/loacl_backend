from fastapi import APIRouter

from app.api.v1.endpoints import (
    assistant_communication,
    assistant_streaming,
    assistants,
    auth,
)

api_router = APIRouter()

# Import and include other routers here
# Example:
# from .endpoints import users, chat, assistants
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# api_router.include_router(assistants.router, prefix="/assistants", tags=["assistants"])

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(assistants.router, prefix="/assistants", tags=["assistants"])
api_router.include_router(
    assistant_communication.router,
    prefix="/assistant-communication",
    tags=["assistant-communication"],
)
api_router.include_router(
    assistant_streaming.router,
    prefix="/assistant-streaming",
    tags=["assistant-streaming"],
)
