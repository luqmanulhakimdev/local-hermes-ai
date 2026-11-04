import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "agent.db"


class Memory:
    def __init__(self, db_path=None):
        target_path = Path(db_path) if db_path else DB_PATH
        target_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(target_path)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_key TEXT UNIQUE NOT NULL,
                memory_value TEXT NOT NULL
            )
        """)

        self.connection.commit()

    def save_message(self, role, content):
        self.connection.execute(
            "INSERT INTO messages (role, content) VALUES (?, ?)",
            (role, content)
        )
        self.connection.commit()

    def get_recent_messages(self, limit=20):
        rows = self.connection.execute(
            """
            SELECT role, content FROM (
                SELECT id, role, content
                FROM messages
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (limit,)
        ).fetchall()

        return [
            {"role": role, "content": content}
            for role, content in rows
        ]

    def remember(self, key, value):
        self.connection.execute(
            """
            INSERT INTO memories (memory_key, memory_value)
            VALUES (?, ?)
            ON CONFLICT(memory_key)
            DO UPDATE SET memory_value = excluded.memory_value
            """,
            (key, value)
        )
        self.connection.commit()

    def get_memories(self):
        rows = self.connection.execute(
            "SELECT memory_key, memory_value FROM memories"
        ).fetchall()

        return dict(rows)

    def forget(self, key):
        cursor = self.connection.execute(
            "DELETE FROM memories WHERE memory_key = ?",
            (key,)
        )
        self.connection.commit()

        return cursor.rowcount > 0

    def clear_history(self):
        self.connection.execute("DELETE FROM messages")
        self.connection.commit()

    def close(self):
        self.connection.close()
