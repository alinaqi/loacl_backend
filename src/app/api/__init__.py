"""
API routes module.
"""

from fastapi import APIRouter

from app.api import auth, threads

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(threads.router, prefix="/threads", tags=["threads"])
