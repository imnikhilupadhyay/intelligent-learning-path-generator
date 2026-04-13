"""Logging configuration helpers."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any


def configure_logging(level: str | None = None) -> None:
    """Configure root logging for CLI, API, and workers.

    Args:
        level: Log level name (e.g. ``INFO``). Defaults to ``LOG_LEVEL`` env or INFO.
    """
    lvl = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, lvl, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger.

    Args:
        name: Typically ``__name__``.

    Returns:
        Configured :class:`logging.Logger`.
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, msg: str, exc_info: Any) -> None:
    """Log an exception with consistent formatting.

    Args:
        logger: Target logger.
        msg: Context message.
        exc_info: Exception instance or ``True`` for last exception.
    """
    logger.exception(msg, exc_info=exc_info)
