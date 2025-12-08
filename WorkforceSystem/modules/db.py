from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
import sys
from pathlib import Path

# Ensure project root is on sys.path when this module is executed directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import mysql.connector
from mysql.connector import MySQLConnection

from config.db_config import DatabaseConfig


class Database:
    """MySQL helper that owns connection lifecycle and schema bootstrapping."""

    def __init__(self, config: DatabaseConfig):
        self.config = config

    @contextmanager
    def connect(self) -> Iterator[MySQLConnection]:
        conn = mysql.connector.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.user,
            password=self.config.password,
            database=self.config.database,
            connection_timeout=self.config.timeout,
            autocommit=False,
        )
        try:
            yield conn
        finally:
            conn.close()

    def initialize(self) -> None:
        """
        Initialization is a no-op against your existing schema.
        (Legacy bootstrap disabled to avoid conflicting with current tables/views.)
        """
        return


__all__ = ["Database"]
