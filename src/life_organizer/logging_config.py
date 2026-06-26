"""Logging configuration for structured logging."""

import logging
import sys
from typing import ClassVar

from life_organizer.config import Settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with colors in development."""

    # ANSI color codes
    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, use_colors: bool = True) -> None:
        """Initialize the formatter.

        Args:
            use_colors: Whether to use color output
        """
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with structured output.

        Args:
            record: Log record to format

        Returns:
            Formatted log string
        """
        # Format: [LEVEL] timestamp - name - message
        level = record.levelname
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        name = record.name
        message = record.getMessage()

        # Add color if enabled
        if self.use_colors and level in self.COLORS:
            level_colored = f"{self.COLORS[level]}{level:8}{self.COLORS['RESET']}"
            formatted = f"[{level_colored}] {timestamp} - {name} - {message}"
        else:
            formatted = f"[{level:8}] {timestamp} - {name} - {message}"

        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_logging(settings: Settings) -> None:
    """Configure application logging.

    Args:
        settings: Application settings
    """
    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Use colors in debug mode
    formatter = StructuredFormatter(use_colors=settings.debug)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reduce verbosity of some third-party loggers.
    # uvicorn.access is left at WARNING because RequestLoggingMiddleware emits a
    # richer per-request line (status + duration); enabling both would duplicate.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
