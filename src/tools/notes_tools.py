
import sqlite3
from pathlib import Path
from contextlib import closing


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "automation.db"

MAX_NOTE_SIZE = 20_000
MAX_SEARCH_RESULTS = 20


def _get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
    except Exception:
        connection.close()
        raise

    return connection


def save_note(content: str) -> str:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Note content must not be empty")

    if len(content) > MAX_NOTE_SIZE:
        raise ValueError("Note exceeds the maximum allowed size")

    with closing(_get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO notes (content) VALUES (?)",
                (content.strip(),),
            )
            note_id = cursor.lastrowid

    return f"Note saved successfully. ID: {note_id}"


def search_notes(query: str) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query must not be empty")

    with closing(_get_connection()) as connection:
        with connection:
            rows = connection.execute(
                """
                SELECT id, content, created_at
                FROM notes
                WHERE content LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (f"%{query.strip()}%", MAX_SEARCH_RESULTS),
            ).fetchall()

    return [dict(row) for row in rows]
