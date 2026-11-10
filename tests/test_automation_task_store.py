import tempfile
import unittest
from pathlib import Path

from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.task_store import TaskStore


class TestTaskStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.store = TaskStore(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_get_task(self):
        task = TaskPlan(
            description="Test task",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="list_files",
                    arguments={},
                ),
                TaskStep(
                    step_id=2,
                    tool="save_note",
                    arguments={"content": "$step_1"},
                ),
            ],
        )

        self.store.save_task(task)

        loaded = self.store.get_task(task.task_id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.task_id, task.task_id)
        self.assertEqual(loaded.description, task.description)
        self.assertEqual(loaded.status, TaskStatus.PENDING)
        self.assertEqual(len(loaded.steps), 2)

        self.assertEqual(loaded.steps[0].tool, "list_files")
        self.assertEqual(loaded.steps[1].tool, "save_note")
        self.assertEqual(
            loaded.steps[1].arguments,
            {"content": "$step_1"},
        )

    def test_update_task_state(self):
        task = TaskPlan(
            description="Test task",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="list_files",
                    arguments={},
                ),
            ],
        )

        self.store.save_task(task)

        task.status = TaskStatus.COMPLETED
        task.steps[0].status = StepStatus.COMPLETED
        task.steps[0].output = ["a.md", "b.md"]

        self.store.save_task(task)

        loaded = self.store.get_task(task.task_id)

        self.assertEqual(loaded.status, TaskStatus.COMPLETED)
        self.assertEqual(
            loaded.steps[0].status,
            StepStatus.COMPLETED,
        )
        self.assertEqual(
            loaded.steps[0].output,
            ["a.md", "b.md"],
        )

    def test_step_error_is_persisted(self):
        task = TaskPlan(
            description="Test task",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="list_files",
                    arguments={},
                ),
            ],
        )

        task.status = TaskStatus.FAILED
        task.steps[0].status = StepStatus.FAILED
        task.steps[0].error = "Something went wrong"

        self.store.save_task(task)

        loaded = self.store.get_task(task.task_id)

        self.assertEqual(loaded.status, TaskStatus.FAILED)
        self.assertEqual(
            loaded.steps[0].status,
            StepStatus.FAILED,
        )
        self.assertEqual(
            loaded.steps[0].error,
            "Something went wrong",
        )

    def test_missing_task_returns_none(self):
        result = self.store.get_task("does-not-exist")

        self.assertIsNone(result)

    def test_empty_task_id_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.get_task("")


if __name__ == "__main__":
    unittest.main()