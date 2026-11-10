import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.automation.models import (
    StepStatus,
    TaskPlan,
    TaskStatus,
    TaskStep,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "automation.db"


class TaskStore:
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_tasks (
                    task_id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_task_steps (
                    task_id TEXT NOT NULL,
                    step_id INTEGER NOT NULL,
                    tool TEXT NOT NULL,
                    arguments TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output TEXT,
                    error TEXT,
                    PRIMARY KEY (task_id, step_id),
                    FOREIGN KEY (task_id)
                        REFERENCES automation_tasks(task_id)
                        ON DELETE CASCADE
                )
                """
            )

    def save_task(self, task: TaskPlan) -> None:
        if not isinstance(task, TaskPlan):
            raise TypeError("task must be a TaskPlan")

        timestamp = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO automation_tasks (
                    task_id,
                    description,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    description = excluded.description,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    task.task_id,
                    task.description,
                    task.status.value,
                    timestamp,
                    timestamp,
                ),
            )

            connection.execute(
                """
                DELETE FROM automation_task_steps
                WHERE task_id = ?
                """,
                (task.task_id,),
            )

            for step in task.steps:
                connection.execute(
                    """
                    INSERT INTO automation_task_steps (
                        task_id,
                        step_id,
                        tool,
                        arguments,
                        status,
                        output,
                        error
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.task_id,
                        step.step_id,
                        step.tool,
                        json.dumps(
                            step.arguments,
                            ensure_ascii=False,
                        ),
                        step.status.value,
                        json.dumps(
                            step.output,
                            ensure_ascii=False,
                            default=str,
                        )
                        if step.output is not None
                        else None,
                        step.error,
                    ),
                )

    def get_task(self, task_id: str) -> TaskPlan | None:
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must not be empty")

        with self._connect() as connection:
            task_row = connection.execute(
                """
                SELECT task_id, description, status
                FROM automation_tasks
                WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()

            if task_row is None:
                return None

            step_rows = connection.execute(
                """
                SELECT
                    step_id,
                    tool,
                    arguments,
                    status,
                    output,
                    error
                FROM automation_task_steps
                WHERE task_id = ?
                ORDER BY step_id
                """,
                (task_id,),
            ).fetchall()

        steps = []

        for row in step_rows:
            output = (
                json.loads(row["output"])
                if row["output"] is not None
                else None
            )

            steps.append(
                TaskStep(
                    step_id=row["step_id"],
                    tool=row["tool"],
                    arguments=json.loads(row["arguments"]),
                    status=StepStatus(row["status"]),
                    output=output,
                    error=row["error"],
                )
            )

        return TaskPlan(
            description=task_row["description"],
            steps=steps,
            task_id=task_row["task_id"],
            status=TaskStatus(task_row["status"]),
        )