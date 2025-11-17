"""Logging configuration helpers."""

import logging
from pathlib import Path

from .config import settings


def configure_logging() -> None:
    """Configure application level logging."""

    log_dir = Path(settings.database_url.replace("sqlite:///", "")).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "level": logging.DEBUG if settings.debug else logging.INFO,
        "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    }

    logging.basicConfig(**logging_config)


__all__ = ["configure_logging"]

