"""
Logging configuration module.
"""

import logging
import sys
from typing import Any

import structlog

from app.core.config import get_settings

settings = get_settings()


def configure_logging() -> None:
    """Configure structured logging for the application."""

    # Set logging level based on environment
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            (
                structlog.dev.ConsoleRenderer()
                if settings.DEBUG
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.DEBUG else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(*args: Any, **kwargs: Any) -> structlog.BoundLogger:
    """
    Get a configured logger instance.

    Returns:
        structlog.BoundLogger: Configured logger instance
    """
    return structlog.get_logger(*args, **kwargs)
