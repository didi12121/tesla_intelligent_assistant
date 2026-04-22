from contextlib import contextmanager
from typing import Any, Iterable, Optional

import pymysql

from config import MYSQL_CONFIG


def get_conn():
    """
    获取一个新的 MySQL 连接
    """
    return pymysql.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        charset=MYSQL_CONFIG.get("charset", "utf8mb4"),
        autocommit=MYSQL_CONFIG.get("autocommit", True),
        cursorclass=pymysql.cursors.DictCursor,
    )


class Database:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or MYSQL_CONFIG

    @contextmanager
    def connection(self):
        conn = pymysql.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()

    def execute(self, sql: str, params: Optional[Iterable[Any]] = None) -> int:
        with self.connection() as conn:
            with conn.cursor() as cursor:
                affected = cursor.execute(sql, params or ())
            conn.commit()
            return affected

    def fetchone(self, sql: str, params: Optional[Iterable[Any]] = None) -> Optional[dict]:
        with self.connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchone()

    def fetchall(self, sql: str, params: Optional[Iterable[Any]] = None) -> list[dict]:
        with self.connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(sql, params or ())
                return list(cursor.fetchall())

