"""Structured logging with structlog."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from tfo_mcp.infrastructure.config import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """Configure structured logging."""
    # Determine log level
    level = getattr(logging, config.level.upper(), logging.INFO)

    # Configure processors
    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if config.format == "json":
        # JSON format for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console format for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    output = sys.stderr if config.output == "stderr" else sys.stdout
    handler: logging.Handler
    if config.output not in ("stderr", "stdout"):
        # File output
        handler = logging.FileHandler(config.output)
    else:
        handler = logging.StreamHandler(output)

    logging.basicConfig(
        format="%(message)s",
        level=level,
        handlers=[handler],
    )

    # Set log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]
