"""
LOACL Backend API
Main application module.
"""

import logging
from typing import Dict

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.api.auth import router as auth_router
from app.api.files import router as files_router
from app.api.messages import router as messages_router
from app.core.config import get_settings
from app.core.di import RequestScopeMiddleware
from app.core.logging import configure_logging
from app.utils.logging import setup_logging
from app.utils.middleware import RequestLoggingMiddleware

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


def custom_openapi():
    """
    Generate custom OpenAPI schema for the application.

    Returns:
        dict: OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.PROJECT_DESCRIPTION,
        routes=app.routes,
        tags=[
            {"name": "Health", "description": "Health check endpoints"},
            {
                "name": "Authentication",
                "description": "Authentication related endpoints",
            },
            {"name": "Threads", "description": "Thread management endpoints"},
            {"name": "Messages", "description": "Message management endpoints"},
            {"name": "Files", "description": "File management endpoints"},
            {"name": "Assistant", "description": "Assistant configuration endpoints"},
        ],
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    logger.info(
        "Creating FastAPI application",
        extra={
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENV,
        },
    )

    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    )

    # Add request logging middleware
    application.add_middleware(RequestLoggingMiddleware)

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add request scope middleware
    application.add_middleware(RequestScopeMiddleware)

    # Configure logging
    configure_logging()

    # Include routers
    application.include_router(auth_router)
    application.include_router(messages_router)
    application.include_router(files_router)

    @application.get(
        "/health",
        tags=["Health"],
        summary="Health Check",
        response_model=Dict[str, str],
        status_code=status.HTTP_200_OK,
        responses={
            200: {
                "description": "Successful Response",
                "content": {"application/json": {"example": {"status": "ok"}}},
            }
        },
    )
    async def health_check() -> Dict[str, str]:
        """
        Perform a health check of the API.

        Returns:
            Dict[str, str]: Health status of the API
        """
        logger.debug("Health check requested")
        return {"status": "ok"}

    return application


app = create_application()
app.openapi = custom_openapi
