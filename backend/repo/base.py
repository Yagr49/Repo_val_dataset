import logging
from abc import ABC
from contextlib import contextmanager

import psycopg2


@contextmanager
def get_cursor(host: str = "pg"):
    """Get a connection/cursor to the database.

    :returns: Tuple of connection and cursor.
    """
    try:
        conn = psycopg2.connect(
            host=host, port=5432, database="postgres", user="postgres", password="admin"
        )
        yield conn, conn.cursor()
    except psycopg2.DatabaseError as error:
        logging.error(f"Connection to database is not available: {error}")
    finally:
        conn.close()


class BaseRepo(ABC):

    @staticmethod
    def execute_query(query, values=None, fetchone=False):
        """Общий метод для выполнения запросов к БД"""
        with get_cursor() as (conn, c):
            c.execute(query, values)
            result = c.fetchone() if fetchone else c.fetchall()
            conn.commit()
            return result

    @staticmethod
    def execute_write_query(query, values=None, many=False):
        """Выполняет записи без возврата."""
        with get_cursor() as (conn, c):
            if not many:
                c.execute(query, values)
            else:
                c.executemany(query, values)
            conn.commit()
