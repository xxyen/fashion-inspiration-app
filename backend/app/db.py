import sqlite3
from pathlib import Path
from .config import DATABASE_PATH


SCHEMA_PATH = Path(__file__).with_name("schema.sql")

IMAGE_COLUMNS = {
    "metadata_json": "TEXT NOT NULL DEFAULT '{}'",
    "designer_tags_json": "TEXT NOT NULL DEFAULT '[]'",
    "designer_notes": "TEXT",
    "designer": "TEXT",
    "continent": "TEXT",
    "country": "TEXT",
    "city": "TEXT",
    "captured_at": "TEXT",
    "updated_at": "TEXT",
}


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        table_exists = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'images'"
        ).fetchone()
        if table_exists:
            ensure_image_columns(connection)
        connection.executescript(SCHEMA_PATH.read_text())
        ensure_image_columns(connection)


def ensure_image_columns(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(images)").fetchall()
    }
    for column, definition in IMAGE_COLUMNS.items():
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE images ADD COLUMN {column} {definition}")
