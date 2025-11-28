from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = 3306
DEFAULT_DB_USER = "root"
DEFAULT_DB_PASSWORD = "Sic300445!"
DEFAULT_DB_NAME = "workforceV3"
DEFAULT_DB_TIMEOUT = 30


@dataclass(frozen=True)
class DatabaseConfig:
    """Database settings loaded from environment or sensible defaults."""

    host: str = DEFAULT_DB_HOST
    port: int = DEFAULT_DB_PORT
    user: str = DEFAULT_DB_USER
    password: str = DEFAULT_DB_PASSWORD
    database: str = DEFAULT_DB_NAME
    timeout: int = DEFAULT_DB_TIMEOUT

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Build a config instance using environment overrides when present."""
        return cls(
            host=os.getenv("WORKFORCE_DB_HOST", DEFAULT_DB_HOST),
            port=int(os.getenv("WORKFORCE_DB_PORT", DEFAULT_DB_PORT)),
            user=os.getenv("WORKFORCE_DB_USER", DEFAULT_DB_USER),
            password=os.getenv("WORKFORCE_DB_PASSWORD", DEFAULT_DB_PASSWORD),
            database=os.getenv("WORKFORCE_DB_NAME", DEFAULT_DB_NAME),
            timeout=int(os.getenv("WORKFORCE_DB_TIMEOUT", DEFAULT_DB_TIMEOUT)),
        )


__all__ = [
    "DatabaseConfig",
    "DEFAULT_DB_HOST",
    "DEFAULT_DB_PORT",
    "DEFAULT_DB_USER",
    "DEFAULT_DB_PASSWORD",
    "DEFAULT_DB_NAME",
    "DEFAULT_DB_TIMEOUT",
]
