import tempfile
import unittest
from pathlib import Path

from src.automation.executor import TaskExecutor
from src.automation.models import TaskPlan, TaskStep, TaskStatus, StepStatus
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestTaskExecutorPersistence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "automation.db"

        self.registry = ToolRegistry()

        self.registry.register(
            ToolDefinition(
                name="read_text",
                description="Return sample document content",
                handler=lambda path: f"Content from {path}",
                required_arguments={"path"},
            )
        )

        self.store = TaskStore(db_path=self.db_path)

        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.store,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_completed_task_is_persisted(self):
        task = TaskPlan(
            description="Read a document",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_text",
                    arguments={"path": "documents/example.md"},
                )
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.COMPLETED)

        stored = self.store.get_task(task.task_id)

        self.assertIsNotNone(stored)
        self.assertEqual(
            stored.status,
            TaskStatus.COMPLETED,
        )
        self.assertEqual(
            stored.steps[0].status,
            StepStatus.COMPLETED,
        )
        self.assertEqual(
            stored.steps[0].output,
            "Content from documents/example.md",
        )

    def test_failed_task_is_persisted(self):
        self.registry.register(
            ToolDefinition(
                name="failing_tool",
                description="Always fails",
                handler=lambda: (_ for _ in ()).throw(
                    RuntimeError("Something went wrong")
                ),
                required_arguments=set(),
            )
        )

        task = TaskPlan(
            description="Run failing tool",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="failing_tool",
                )
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)

        stored = self.store.get_task(task.task_id)

        self.assertIsNotNone(stored)
        self.assertEqual(
            stored.status,
            TaskStatus.FAILED,
        )
        self.assertEqual(
            stored.steps[0].status,
            StepStatus.FAILED,
        )
        self.assertIn(
            "RuntimeError",
            stored.steps[0].error,
        )


if __name__ == "__main__":
    unittest.main()