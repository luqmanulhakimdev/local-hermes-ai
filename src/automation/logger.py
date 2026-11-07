import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "automation.db"


class TaskLogger:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS automation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    step_id INTEGER,
                    event TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                )
            """)

    def log_event(self, task_id, event, step_id=None, details=None):
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must not be empty")

        if not isinstance(event, str) or not event.strip():
            raise ValueError("event must not be empty")

        details_json = json.dumps(details, ensure_ascii=False, default=str)
        timestamp = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO automation_logs
                    (task_id, step_id, event, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_id, step_id, event, details_json, timestamp),
            )

    def get_task_logs(self, task_id):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT task_id, step_id, event, details, created_at
                FROM automation_logs
                WHERE task_id = ?
                ORDER BY id
                """,
                (task_id,),
            ).fetchall()

        return [
            {
                **dict(row),
                "details": json.loads(row["details"]),
            }
            for row in rows
        ]