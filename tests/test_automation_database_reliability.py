import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.task_store import TaskStore


class TestDatabaseReliability(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.store = TaskStore(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_foreign_key_enforcement(self):
        # Directly attempt to insert a step with non-existent task_id
        with self.store._connection() as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """
                    INSERT INTO automation_task_steps
                        (task_id, step_id, tool, arguments, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    ("non_existent_task", 1, "tool", "{}", "pending"),
                )

    def test_transaction_rollback_on_failure(self):
        task = TaskPlan(
            description="Initial task",
            steps=[TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED)],
            status=TaskStatus.COMPLETED,
        )
        self.store.save_task(task)

        # Attempt to save a task whose second step cannot be JSON-serialized
        task.steps.append(
            TaskStep(
                step_id=2,
                tool="broken_tool",
                arguments={"bad": object()},
            )
        )

        with self.assertRaises(TypeError):
            self.store.save_task(task)

        # Confirm rollback: previous task state in database must remain consistent
        reloaded = self.store.get_task(task.task_id)
        self.assertIsNotNone(reloaded)
        self.assertEqual(len(reloaded.steps), 1)
        self.assertEqual(reloaded.steps[0].tool, "tool1")

    def test_missing_task_returns_none(self):
        self.assertIsNone(self.store.get_task("non_existent_id"))

    def test_invalid_task_id_rejected(self):
        with self.assertRaises(ValueError):
            self.store.get_task("")
        with self.assertRaises(ValueError):
            self.store.get_task("   ")
        with self.assertRaises(TypeError):
            self.store.get_task(123)

    def test_invalid_task_type_rejected(self):
        with self.assertRaises(TypeError):
            self.store.save_task("not_a_task")

    def test_task_update_consistency(self):
        task = TaskPlan(
            description="Task to update",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.PENDING),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.PENDING),
            ],
            status=TaskStatus.PENDING,
        )
        self.store.save_task(task)

        # Update step 1 to completed
        task.steps[0].status = StepStatus.COMPLETED
        task.steps[0].output = {"result": 42}
        task.status = TaskStatus.RUNNING
        self.store.save_task(task)

        loaded = self.store.get_task(task.task_id)
        self.assertEqual(loaded.status, TaskStatus.RUNNING)
        self.assertEqual(loaded.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(loaded.steps[0].output, {"result": 42})
        self.assertEqual(loaded.steps[1].status, StepStatus.PENDING)

    def test_corrupted_task_without_steps_fails_closed(self):
        with self.store._connection() as connection:
            connection.execute(
                """
                INSERT INTO automation_tasks
                    (task_id, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("corrupt_task", "Corrupt without steps", "pending", "2026-01-01", "2026-01-01"),
            )

        with self.assertRaises(ValueError):
            self.store.get_task("corrupt_task")


if __name__ == "__main__":
    unittest.main()
