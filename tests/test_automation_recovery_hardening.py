import tempfile
import unittest
from pathlib import Path

from src.automation.executor import TaskExecutor
from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestRecoveryHardening(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="step1_tool",
                description="Step 1 tool",
                handler=lambda: "out_1",
                required_arguments=set(),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="step2_tool",
                description="Step 2 tool",
                handler=lambda text: f"echo_{text}",
                required_arguments={"text"},
            )
        )
        self.task_store = TaskStore(self.db_path)
        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_resume_missing_task_fails(self):
        with self.assertRaises(ValueError) as ctx:
            self.executor.resume("non_existent_id")
        self.assertIn("Task not found", str(ctx.exception))

    def test_resume_completed_task_fails(self):
        task = TaskPlan(
            description="Completed",
            steps=[TaskStep(step_id=1, tool="step1_tool", status=StepStatus.COMPLETED, output="out_1")],
            status=TaskStatus.COMPLETED,
        )
        self.task_store.save_task(task)

        with self.assertRaises(ValueError) as ctx:
            self.executor.resume(task.task_id)
        self.assertIn("Completed tasks cannot be resumed", str(ctx.exception))

    def test_resume_failed_task_fails(self):
        task = TaskPlan(
            description="Failed",
            steps=[TaskStep(step_id=1, tool="step1_tool", status=StepStatus.FAILED, error="err")],
            status=TaskStatus.FAILED,
        )
        self.task_store.save_task(task)

        with self.assertRaises(ValueError) as ctx:
            self.executor.resume(task.task_id)
        self.assertIn("Failed tasks cannot be resumed", str(ctx.exception))

    def test_resume_awaiting_approval_task_fails(self):
        task = TaskPlan(
            description="Awaiting approval",
            steps=[TaskStep(step_id=1, tool="step1_tool", status=StepStatus.AWAITING_APPROVAL)],
            status=TaskStatus.AWAITING_APPROVAL,
        )
        self.task_store.save_task(task)

        with self.assertRaises(ValueError) as ctx:
            self.executor.resume(task.task_id)
        self.assertIn("awaiting approval cannot be resumed", str(ctx.exception))

    def test_resume_task_with_step_awaiting_approval_fails(self):
        # Adversarial state: task marked RUNNING but a step is AWAITING_APPROVAL
        task = TaskPlan(
            description="Sneaky approval",
            steps=[
                TaskStep(step_id=1, tool="step1_tool", status=StepStatus.COMPLETED, output="out_1"),
                TaskStep(step_id=2, tool="step2_tool", arguments={"text": "$step_1"}, status=StepStatus.AWAITING_APPROVAL),
            ],
            status=TaskStatus.RUNNING,
        )
        self.task_store.save_task(task)

        with self.assertRaises(ValueError) as ctx:
            self.executor.resume(task.task_id)
        self.assertIn("awaiting approval", str(ctx.exception))

    def test_resume_with_missing_referenced_output_fails(self):
        # Step 1 was supposedly completed but has None output, and Step 2 references $step_1
        task = TaskPlan(
            description="Missing output ref",
            steps=[
                TaskStep(step_id=1, tool="step1_tool", status=StepStatus.COMPLETED, output=None),
                TaskStep(step_id=2, tool="step2_tool", arguments={"text": "$step_1"}, status=StepStatus.PENDING),
            ],
            status=TaskStatus.RUNNING,
        )
        self.task_store.save_task(task)

        result = self.executor.resume(task.task_id)
        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertIn("unavailable", result.steps[1].error)

    def test_interrupted_running_step_is_safely_reexecuted(self):
        # Step 1 is completed, Step 2 was marked RUNNING when crash occurred
        task = TaskPlan(
            description="Interrupted running step",
            steps=[
                TaskStep(step_id=1, tool="step1_tool", status=StepStatus.COMPLETED, output="val1"),
                TaskStep(step_id=2, tool="step2_tool", arguments={"text": "$step_1"}, status=StepStatus.RUNNING),
            ],
            status=TaskStatus.RUNNING,
        )
        self.task_store.save_task(task)

        result = self.executor.resume(task.task_id)

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(result.steps[1].status, StepStatus.COMPLETED)
        self.assertEqual(result.steps[1].output, "echo_val1")


if __name__ == "__main__":
    unittest.main()
