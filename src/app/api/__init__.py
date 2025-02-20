"""
API routes module.
"""

from fastapi import APIRouter

from app.api import analytics, auth, health, threads, webhooks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(threads.router, prefix="/threads", tags=["threads"])
api_router.include_router(webhooks.router, tags=["webhooks"])
api_router.include_router(health.router)
api_router.include_router(analytics.router)
