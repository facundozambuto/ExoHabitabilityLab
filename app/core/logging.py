"""
Logging configuration for ExoHabitabilityLab.

Provides structured logging with configurable levels and formats.
"""

import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return the application logger.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
        
    Returns:
        logging.Logger: Configured logger instance
    """
    log_level = level or settings.log_level
    
    default_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    log_format = format_string or default_format
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    
    # Create application logger
    logger = logging.getLogger("exohabitabilitylab")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name for the logger (typically __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(f"exohabitabilitylab.{name}")


# Initialize default logger
logger = setup_logging()
