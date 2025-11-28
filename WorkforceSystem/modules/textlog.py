from __future__ import annotations

import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "logs" / "workforce.log"

def get_logger(name: str = "workforce") -> logging.Logger:
    """Return a configured logger that writes each activity with timestamp, module, and message."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(LOG_PATH)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))

    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger

__all__ = ["get_logger", "LOG_PATH"]
