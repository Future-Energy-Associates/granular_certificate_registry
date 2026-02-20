import datetime
import json
import logging
import logging.config
import traceback
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator

from .settings import settings

# Thread-safe context variable for storing business context
_business_ctx: ContextVar[dict[str, Any]] = ContextVar("business_ctx", default={})


@contextmanager
def log_context(**kwargs: Any) -> Generator[dict[str, Any], None, None]:
    """Context manager that injects contextual variables into all log calls within its scope.

    Structured logging configuration with context manager support.

    This module provides a contextvars-based logging context manager that allows
    injecting contextual variables into all log calls within its scope. The
    StructuredFormatter outputs JSON logs suitable for log aggregation systems.

    Args:
        **kwargs: Key-value pairs to add to the logging context.

    Yields:
        The current context dictionary (merged with any new kwargs).

    Example:
        with log_context(route="/api/endpoint", user_id=123):
            logger.info("Processing request")  # Includes route and user_id
            with log_context(device_id=456):
                logger.info("Device operation")  # Includes route, user_id, and device_id
    """
    # Merge new context with existing context
    current_ctx = _business_ctx.get()
    new_ctx = {**current_ctx, **kwargs}
    token = _business_ctx.set(new_ctx)
    try:
        yield new_ctx
    finally:
        _business_ctx.reset(token)


def get_log_context() -> dict[str, Any]:
    """Retrieve the current logging context.

    Returns:
        A dictionary containing all context variables set via log_context().
    """
    return _business_ctx.get()


class StructuredFormatter(logging.Formatter):
    """JSON formatter that includes context variables and source location.

    Outputs structured JSON logs with:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level name
    - logger: Logger name
    - message: Log message
    - source: Source location (file, line, function)
    - context: All variables from log_context()
    - extra: Any additional fields passed via extra={}
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON-formatted string containing the structured log data.
        """
        # Build the base log structure
        log_data: dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, tz=datetime.timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add business context from contextvars
        ctx = get_log_context()
        if ctx:
            log_data["context"] = ctx

        # Add any extra fields passed to the logger
        # Exclude standard LogRecord attributes
        standard_attrs = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "taskName",
            "message",
        }

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in standard_attrs and not key.startswith("_")
        }

        if extra_fields:
            log_data["extra"] = extra_fields

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, default=str)


def set_logger_and_children_level(
    logger_instance: logging.Logger, level: int | str
) -> None:
    """Set the level for a logger and all its children.

    Args:
        logger_instance: The logger instance to modify.
        level: The logging level to set (e.g., logging.DEBUG or "DEBUG").
    """
    logger_instance.setLevel(level)

    # Set handler levels
    for handler in logger_instance.handlers:
        handler.setLevel(level)

    # Get all existing loggers
    existing_loggers = [
        name
        for name in logging.root.manager.loggerDict
        if name.startswith(logger_instance.name + ".")
    ]

    # Set level for all child loggers
    for child_logger_name in existing_loggers:
        child_logger = logging.getLogger(child_logger_name)
        child_logger.setLevel(level)
        for handler in child_logger.handlers:
            handler.setLevel(level)


# Define the logging configuration with structured JSON output
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
        "structured": {
            "()": StructuredFormatter,
        },
    },
    "handlers": {
        "default": {
            "level": settings.LOG_LEVEL,
            "formatter": "structured",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": settings.LOG_LEVEL,
            "propagate": True,
        },
    },
}

# Apply the logging configuration
logging.config.dictConfig(LOGGING_CONFIG)

# Create a global logger instance
logger = logging.getLogger(__name__)
