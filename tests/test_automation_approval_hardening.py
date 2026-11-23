import tempfile
import unittest
from pathlib import Path

from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger
from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestApprovalHardening(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="sensitive_tool",
                description="Sensitive tool",
                handler=lambda: "done",
                required_arguments=set(),
                requires_approval=True,
            )
        )
        self.task_store = TaskStore(self.db_path)
        self.logger = TaskLogger(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_approval_handler_fails_closed(self):
        executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
            approval_handler=None,
        )
        task = TaskPlan(
            description="Needs approval without handler",
            steps=[TaskStep(step_id=1, tool="sensitive_tool")],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertIn("Approval required", result.steps[0].error)

    def test_truthy_non_boolean_approval_is_rejected(self):
        # Hostile or buggy approval handler returning truthy non-bools
        truthy_values = ["yes", 1, [True], {"approved": True}, "true"]

        for val in truthy_values:
            with self.subTest(val=val):
                executor = TaskExecutor(
                    registry=self.registry,
                    task_store=self.task_store,
                    logger=self.logger,
                    approval_handler=lambda t, s, a: val,
                )
                task = TaskPlan(
                    description=f"Truthy approval test: {val}",
                    steps=[TaskStep(step_id=1, tool="sensitive_tool")],
                )

                result = executor.execute(task)

                self.assertEqual(result.status, TaskStatus.FAILED)
                self.assertEqual(result.steps[0].status, StepStatus.FAILED)
                self.assertIn("denied", result.steps[0].error.lower())

    def test_explicit_boolean_true_grants_approval(self):
        executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
            approval_handler=lambda t, s, a: True,
        )
        task = TaskPlan(
            description="Valid boolean approval",
            steps=[TaskStep(step_id=1, tool="sensitive_tool")],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(result.steps[0].output, "done")

    def test_exception_in_approval_handler_fails_closed(self):
        def faulty_handler(t, s, a):
            raise RuntimeError("Approval service crashed")

        executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
            approval_handler=faulty_handler,
        )
        task = TaskPlan(
            description="Faulty approval handler",
            steps=[TaskStep(step_id=1, tool="sensitive_tool")],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertIn("RuntimeError", result.steps[0].error)


if __name__ == "__main__":
    unittest.main()
