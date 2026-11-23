import tempfile
import unittest
from pathlib import Path

from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger
from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestCancellation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="step1_tool",
                description="Step 1 tool",
                handler=lambda: "out1",
                required_arguments=set(),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="step2_tool",
                description="Step 2 tool",
                handler=lambda: "out2",
                required_arguments=set(),
            )
        )
        self.task_store = TaskStore(self.db_path)
        self.logger = TaskLogger(self.db_path)
        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cancel_pending_task_before_execution(self):
        task = TaskPlan(
            description="Pending task to cancel",
            steps=[
                TaskStep(step_id=1, tool="step1_tool"),
                TaskStep(step_id=2, tool="step2_tool"),
            ],
        )
        self.task_store.save_task(task)

        success = self.executor.cancel(task.task_id)
        self.assertTrue(success)

        stored = self.task_store.get_task(task.task_id)
        self.assertEqual(stored.status, TaskStatus.CANCELLED)
        # Pending steps remain pending
        self.assertEqual(stored.steps[0].status, StepStatus.PENDING)
        self.assertEqual(stored.steps[1].status, StepStatus.PENDING)

        # Check log
        logs = self.logger.get_task_logs(task.task_id)
        cancelled_logs = [l for l in logs if l["event"] == "task_cancelled"]
        self.assertEqual(len(cancelled_logs), 1)

    def test_cancel_between_steps(self):
        executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
        )

        def step1_handler():
            executor.cancel(task.task_id)
            return "out1"

        self.registry.register(
            ToolDefinition(
                name="step1_cancel",
                description="Cancels task during step 1",
                handler=step1_handler,
                required_arguments=set(),
            )
        )

        task = TaskPlan(
            description="Two step task cancelled between steps",
            steps=[
                TaskStep(step_id=1, tool="step1_cancel"),
                TaskStep(step_id=2, tool="step2_tool"),
            ],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.CANCELLED)
        # Step 1 should be completed, step 2 should remain pending
        self.assertEqual(result.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(result.steps[1].status, StepStatus.PENDING)

        # Persisted state matches
        stored = self.task_store.get_task(task.task_id)
        self.assertEqual(stored.status, TaskStatus.CANCELLED)
        self.assertEqual(stored.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(stored.steps[1].status, StepStatus.PENDING)

        # Check logs
        logs = self.logger.get_task_logs(task.task_id)
        cancelled_logs = [l for l in logs if l["event"] == "task_cancelled"]
        self.assertTrue(len(cancelled_logs) >= 1)

    def test_resume_cancelled_task_succeeds(self):
        # Setup cancelled task with step 1 completed, step 2 pending
        task = TaskPlan(
            description="Resume cancelled task",
            steps=[
                TaskStep(step_id=1, tool="step1_tool", status=StepStatus.COMPLETED, output="out1"),
                TaskStep(step_id=2, tool="step2_tool", status=StepStatus.PENDING),
            ],
            status=TaskStatus.CANCELLED,
        )
        self.task_store.save_task(task)

        resumed = self.executor.resume(task.task_id)

        self.assertEqual(resumed.status, TaskStatus.COMPLETED)
        self.assertEqual(resumed.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(resumed.steps[1].status, StepStatus.COMPLETED)
        self.assertEqual(resumed.steps[1].output, "out2")

    def test_cannot_cancel_completed_task(self):
        task = TaskPlan(
            description="Completed task",
            steps=[
                TaskStep(step_id=1, tool="step1_tool", status=StepStatus.COMPLETED, output="out1"),
            ],
            status=TaskStatus.COMPLETED,
        )
        self.task_store.save_task(task)

        with self.assertRaises(ValueError):
            self.executor.cancel(task.task_id)

        stored = self.task_store.get_task(task.task_id)
        self.assertEqual(stored.status, TaskStatus.COMPLETED)

    def test_cannot_cancel_failed_task(self):
        task = TaskPlan(
            description="Failed task",
            steps=[
                TaskStep(step_id=1, tool="step1_tool", status=StepStatus.FAILED, error="Some error"),
            ],
            status=TaskStatus.FAILED,
        )
        self.task_store.save_task(task)

        with self.assertRaises(ValueError):
            self.executor.cancel(task.task_id)

    def test_cannot_cancel_nonexistent_task(self):
        with self.assertRaises(ValueError):
            self.executor.cancel("non-existent-task-id")


if __name__ == "__main__":
    unittest.main()
