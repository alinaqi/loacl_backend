"""Logging configuration for the application.

This module sets up logging with proper formatting and handlers.
"""

import logging
import logging.config
import sys
from typing import Any, Dict

# Configure logging format
LOG_FORMAT: str = (
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# Configure logging settings
LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": LOG_FORMAT,
            "datefmt": DATE_FORMAT,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# Configure logging using dictConfig
logging.config.dictConfig(LOGGING_CONFIG)

# Create and get logger
logger = logging.getLogger("app")

# Set log level based on environment (can be configured via environment variable)
logger.setLevel(logging.DEBUG)  # Default to DEBUG, can be overridden by environment 