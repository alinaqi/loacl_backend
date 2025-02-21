from fastapi import APIRouter
from app.api.v1.endpoints import auth, chatbot

api_router = APIRouter()

# Import and include other routers here
# Example:
# from .endpoints import users, chat, assistants
# api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
# api_router.include_router(assistants.router, prefix="/assistants", tags=["assistants"])

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chatbot.router, prefix="/chatbots", tags=["chatbots"]) 