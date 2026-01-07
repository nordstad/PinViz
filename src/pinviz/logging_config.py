"""Logging configuration for pinviz.

This module provides structured logging using structlog with support for both
human-readable console output and machine-readable JSON output.

Example:
    >>> from pinviz.logging_config import configure_logging, get_logger
    >>> configure_logging(level="INFO", format="console")
    >>> log = get_logger(__name__)
    >>> log.info("operation_started", config_path="diagram.yaml")
"""

import logging
import sys
from typing import Literal

import structlog


def configure_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    format: Literal["json", "console"] = "console",
) -> None:
    """Configure structured logging for the application.

    Args:
        level: Minimum log level to output (DEBUG, INFO, WARNING, ERROR)
        format: Output format - 'json' for machine-readable, 'console' for human-readable

    Example:
        >>> configure_logging(level="DEBUG", format="json")
        >>> log = get_logger(__name__)
        >>> log.debug("detailed_info", value=42)
    """
    # Convert string level to logging constant
    log_level = getattr(logging, level.upper())

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=log_level,
    )

    # Choose renderer based on format
    if format == "json":
        renderer = structlog.processors.JSONRenderer(sort_keys=True)
    else:
        # Console renderer with colors for human-readable output
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog processor pipeline
    structlog.configure(
        processors=[
            # Filter out log entries below the configured level
            structlog.stdlib.filter_by_level,
            # Add the name of the logger to event dict
            structlog.stdlib.add_logger_name,
            # Add log level to event dict
            structlog.stdlib.add_log_level,
            # Perform %-style formatting
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Add timestamp in ISO 8601 format (UTC)
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # If stack_info is true, render current stack trace
            structlog.processors.StackInfoRenderer(),
            # If exc_info is present, render exception with traceback
            structlog.processors.format_exc_info,
            # Decode bytes to Unicode strings
            structlog.processors.UnicodeDecoder(),
            # Add callsite information (filename, function name, line number)
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                }
            ),
            # Final renderer (JSON or Console)
            renderer,
        ],
        # Use stdlib-compatible bound logger
        wrapper_class=structlog.stdlib.BoundLogger,
        # Use stdlib LoggerFactory for output
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Cache logger on first use for performance
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ from the calling module)

    Returns:
        Configured structlog logger with bound context

    Example:
        >>> log = get_logger(__name__)
        >>> log.info("user_action", user_id=123, action="render")
    """
    return structlog.get_logger(name)
