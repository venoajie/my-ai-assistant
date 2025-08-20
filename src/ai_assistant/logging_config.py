# src/ai_assistant/logging_config.py
import logging
import sys
import structlog

def setup_logging(log_level: str = "INFO"):
    """
    Configures structured logging for the entire application.
    """
    # A list of processors that will process log records.
    processors = [
        # Add context variables to the log record.
        structlog.contextvars.merge_contextvars,
        # Add logger-specific context.
        structlog.stdlib.add_logger_name,
        # Add the log level to the record.
        structlog.stdlib.add_log_level,
        # Add a timestamp.
        structlog.processors.TimeStamper(fmt="iso"),
        # If the "exc_info" key is present, render it as a traceback.
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # Render the final log message. For development, ConsoleRenderer is nice.
        # For production, you would switch to JSONRenderer.
        structlog.dev.ConsoleRenderer(colors=True),
    ]

    # Configure the standard logging library to be the sink for structlog.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level.upper(),
    )

    # Configure structlog to wrap the standard library logger.
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )