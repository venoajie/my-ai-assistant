# src/ai_assistant/logging_config.py
import logging
import sys
import structlog
from typing import Optional

from .config import ai_settings

def setup_logging(log_level: Optional[str] = None):
    """
    Configures structured logging for the entire application.
    Allows for a runtime override, otherwise uses the level from config.
    """
    level_to_use = log_level or ai_settings.general.log_level
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(colors=True),
    ]

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level_to_use.upper(),
    )

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )