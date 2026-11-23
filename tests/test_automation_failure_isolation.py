import tempfile
import unittest
from pathlib import Path

from src.automation.executor import TaskExecutor
from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestFailureIsolation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.registry = ToolRegistry()
        self.task_store = TaskStore(self.db_path)

        self.registry.register(
            ToolDefinition(
                name="good_tool_1",
                description="Good tool 1",
                handler=lambda: "result_1",
                required_arguments=set(),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="good_tool_2",
                description="Good tool 2",
                handler=lambda text: f"echo_{text}",
                required_arguments={"text"},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="failing_tool",
                description="Failing tool",
                handler=lambda: 1 / 0,
                required_arguments=set(),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="sensitive_tool",
                description="Sensitive tool",
                handler=lambda: "sensitive",
                required_arguments=set(),
                requires_approval=True,
            )
        )

        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_failure_in_first_step(self):
        task = TaskPlan(
            description="Fail in step 1",
            steps=[
                TaskStep(step_id=1, tool="failing_tool"),
                TaskStep(step_id=2, tool="good_tool_1"),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertIsNone(result.steps[0].output)
        self.assertIn("ZeroDivisionError", result.steps[0].error)
        self.assertEqual(result.steps[1].status, StepStatus.PENDING)
        self.assertIsNone(result.steps[1].output)

    def test_failure_in_middle_step_preserves_first_step_output(self):
        task = TaskPlan(
            description="Fail in step 2",
            steps=[
                TaskStep(step_id=1, tool="good_tool_1"),
                TaskStep(step_id=2, tool="failing_tool"),
                TaskStep(step_id=3, tool="good_tool_1"),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        # Step 1 succeeded and output preserved
        self.assertEqual(result.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(result.steps[0].output, "result_1")
        # Step 2 failed
        self.assertEqual(result.steps[1].status, StepStatus.FAILED)
        self.assertIsNone(result.steps[1].output)
        # Step 3 remained pending
        self.assertEqual(result.steps[2].status, StepStatus.PENDING)

        # Confirm persisted state
        stored = self.task_store.get_task(task.task_id)
        self.assertEqual(stored.status, TaskStatus.FAILED)
        self.assertEqual(stored.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(stored.steps[0].output, "result_1")
        self.assertEqual(stored.steps[1].status, StepStatus.FAILED)
        self.assertEqual(stored.steps[2].status, StepStatus.PENDING)

    def test_failure_in_final_step(self):
        task = TaskPlan(
            description="Fail in step 2 of 2",
            steps=[
                TaskStep(step_id=1, tool="good_tool_1"),
                TaskStep(step_id=2, tool="failing_tool"),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(result.steps[0].output, "result_1")
        self.assertEqual(result.steps[1].status, StepStatus.FAILED)

    def test_approval_denial_failure_isolation(self):
        executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            approval_handler=lambda t, s, a: False,  # Deny
        )
        task = TaskPlan(
            description="Approval denied in step 2",
            steps=[
                TaskStep(step_id=1, tool="good_tool_1"),
                TaskStep(step_id=2, tool="sensitive_tool"),
                TaskStep(step_id=3, tool="good_tool_1"),
            ],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(result.steps[0].output, "result_1")
        self.assertEqual(result.steps[1].status, StepStatus.FAILED)
        self.assertIn("Approval denied", result.steps[1].error)
        self.assertEqual(result.steps[2].status, StepStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
