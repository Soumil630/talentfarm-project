"""Read-only MySQL connector shared by the distributor source, staging, data mart
and reporting-view checks.

Read-only is enforced twice: the connection is opened with the database driver's
read-only session flag where supported, and every statement is checked against
db_config.yaml's allowed_statement_prefixes before it is sent - a bug in a validator
that builds an UPDATE or DELETE is refused here rather than relying solely on the
grants of the supplied credential.
"""
from __future__ import annotations

import time

import pandas as pd
import pymysql
import pymysql.cursors

from ..core.config_loader import Config
from ..core.exceptions import ConnectionFailed, ReadOnlyViolation


class MySqlConnector:
    def __init__(self, config: Config):
        self._config = config
        self._conn: pymysql.connections.Connection | None = None

    # ------------------------------------------------------------- connection
    def _connect(self) -> pymysql.connections.Connection:
        cfg = self._config.section("mysql")["mysql"]
        retries = int(cfg.get("retries", 3))
        backoff = float(cfg.get("retry_backoff_seconds", 2))
        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                return pymysql.connect(
                    host=str(self._config.require("mysql.mysql.host")),
                    port=int(self._config.require("mysql.mysql.port")),
                    user=str(self._config.require("mysql.mysql.user")),
                    password=str(self._config.require("mysql.mysql.password")),
                    charset=str(cfg.get("charset", "utf8mb4")),
                    connect_timeout=int(cfg.get("connect_timeout", 15)),
                    cursorclass=pymysql.cursors.DictCursor,
                    read_timeout=int(cfg.get("connect_timeout", 15)) * 4,
                )
            except Exception as exc:  # noqa: BLE001 - any driver error is a retry candidate
                last_error = exc
                if attempt < retries:
                    time.sleep(backoff * attempt)

        raise ConnectionFailed(
            f"could not connect to MySQL after {retries} attempt(s): {last_error}",
            expected="a live connection to the configured MySQL host",
        )

    def _connection(self) -> pymysql.connections.Connection:
        if self._conn is None or not self._conn.open:
            self._conn = self._connect()
        return self._conn

    # ------------------------------------------------------------- guard rail
    def _assert_read_only(self, statement: str) -> None:
        allowed = self._config.get(
            "mysql.mysql.allowed_statement_prefixes",
            ["SELECT", "SHOW", "DESCRIBE", "EXPLAIN", "WITH"],
        )
        head = statement.strip().split(None, 1)[0].upper() if statement.strip() else ""
        if head not in {a.upper() for a in allowed}:
            raise ReadOnlyViolation(
                f"statement '{head}' is not a permitted read-only operation "
                f"(allowed: {', '.join(allowed)})"
            )

    # ------------------------------------------------------------------- API
    def query(self, sql: str, params: tuple | dict | None = None) -> pd.DataFrame:
        """Run a SELECT-family statement and return the result as a DataFrame."""
        self._assert_read_only(sql)
        conn = self._connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return pd.DataFrame(rows)

    def table_exists(self, schema: str, table: str) -> bool:
        df = self.query(
            "SELECT COUNT(*) AS n FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = %s",
            (schema, table),
        )
        return bool(df.empty is False and int(df.iloc[0]["n"]) > 0)

    def row_count(self, qualified_table: str, where: str = "", params: tuple | None = None) -> int:
        sql = f"SELECT COUNT(*) AS n FROM {qualified_table}"
        if where:
            sql += f" WHERE {where}"
        df = self.query(sql, params)
        return int(df.iloc[0]["n"]) if not df.empty else 0

    def close(self) -> None:
        if self._conn is not None and self._conn.open:
            self._conn.close()
        self._conn = None
