import sqlite3
from pathlib import Path
from .config import DATABASE_PATH


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA_PATH.read_text())
