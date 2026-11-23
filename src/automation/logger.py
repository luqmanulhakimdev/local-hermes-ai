import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "automation.db"

SENSITIVE_KEY_SUBSTRINGS = (
    "password",
    "token",
    "secret",
    "api_key",
    "credential",
    "auth_token",
    "private_key",
)
MAX_LOG_DETAIL_STRING_LENGTH = 10_000


def _sanitize_details(obj, depth: int = 0):
    if depth > 10:
        return "<max_depth_exceeded>"
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            k_str = str(k).lower()
            if any(sub in k_str for sub in SENSITIVE_KEY_SUBSTRINGS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = _sanitize_details(v, depth + 1)
        return sanitized
    if isinstance(obj, list):
        return [_sanitize_details(item, depth + 1) for item in obj]
    if isinstance(obj, str):
        if len(obj) > MAX_LOG_DETAIL_STRING_LENGTH:
            return obj[:MAX_LOG_DETAIL_STRING_LENGTH] + "... [TRUNCATED]"
        return obj
    return obj


class TaskLogger:
    def __init__(self, db_path=None, config=None):
        if db_path:
            self.db_path = Path(db_path)
        elif config and config.db_path:
            self.db_path = Path(config.db_path)
        else:
            self.db_path = DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self):
        with self._connection() as connection:
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
        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string")
        if not task_id.strip():
            raise ValueError("task_id must not be empty")

        if not isinstance(event, str):
            raise TypeError("event must be a string")
        if not event.strip():
            raise ValueError("event must not be empty")

        if step_id is not None:
            if isinstance(step_id, bool) or not isinstance(step_id, int):
                raise TypeError("step_id must be an integer or None")

        sanitized_details = _sanitize_details(details) if details is not None else None
        details_json = json.dumps(sanitized_details, ensure_ascii=False, default=str)
        timestamp = datetime.now(timezone.utc).isoformat()

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO automation_logs
                    (task_id, step_id, event, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_id, step_id, event, details_json, timestamp),
            )

    def get_task_logs(self, task_id):
        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string")
        if not task_id.strip():
            raise ValueError("task_id must not be empty")

        with self._connection() as connection:
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
                "details": json.loads(row["details"]) if row["details"] is not None else None,
            }
            for row in rows
        ]