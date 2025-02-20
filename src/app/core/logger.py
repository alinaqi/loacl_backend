import logging
import sys
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Name for the logger

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only add handler if logger doesn't have any
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", '
            '"module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
