import logging
import logging.config

from .settings import settings


def set_logger_and_children_level(logger_instance, level):
    """Set the level for a logger and all its children."""
    # Get the parent logger
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


# Define the logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "default": {
            "level": settings.LOG_LEVEL,
            "formatter": "standard",
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
