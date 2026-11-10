import tempfile
import unittest
from pathlib import Path

from src.automation.executor import TaskExecutor
from src.automation.models import (
    TaskPlan,
    TaskStep,
    TaskStatus,
    StepStatus,
)
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestTaskExecutorResume(unittest.TestCase):

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

        self.registry.register(
            ToolDefinition(
                name="summarize",
                description="Summarize text",
                handler=lambda text: f"Summary: {text}",
                required_arguments={"text"},
            )
        )

        self.store = TaskStore(db_path=self.db_path)

        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.store,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_resume_runs_pending_task(self):
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

        self.store.save_task(task)

        result = self.executor.resume(task.task_id)

        self.assertEqual(
            result.status,
            TaskStatus.COMPLETED,
        )
        self.assertEqual(
            result.steps[0].status,
            StepStatus.COMPLETED,
        )
        self.assertEqual(
            result.steps[0].output,
            "Content from documents/example.md",
        )

    def test_resume_skips_completed_steps(self):
        calls = []

        def read_text(path):
            calls.append(("read_text", path))
            return f"Content from {path}"

        self.registry = ToolRegistry()

        self.registry.register(
            ToolDefinition(
                name="read_text",
                description="Read text",
                handler=read_text,
                required_arguments={"path"},
            )
        )

        self.registry.register(
            ToolDefinition(
                name="summarize",
                description="Summarize text",
                handler=lambda text: f"Summary: {text}",
                required_arguments={"text"},
            )
        )

        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.store,
        )

        task = TaskPlan(
            description="Read and summarize",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_text",
                    arguments={"path": "documents/example.md"},
                    status=StepStatus.COMPLETED,
                    output="Existing content",
                ),
                TaskStep(
                    step_id=2,
                    tool="summarize",
                    arguments={"text": "$step_1"},
                    status=StepStatus.PENDING,
                ),
            ],
            status=TaskStatus.RUNNING,
        )

        self.store.save_task(task)

        result = self.executor.resume(task.task_id)

        self.assertEqual(
            result.status,
            TaskStatus.COMPLETED,
        )

        self.assertEqual(
            result.steps[0].output,
            "Existing content",
        )

        self.assertEqual(
            result.steps[1].output,
            "Summary: Existing content",
        )

        self.assertEqual(
            calls,
            [],
        )

    def test_resume_reruns_interrupted_running_step(self):
        task = TaskPlan(
            description="Recover interrupted step",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_text",
                    arguments={"path": "documents/example.md"},
                    status=StepStatus.RUNNING,
                )
            ],
            status=TaskStatus.RUNNING,
        )

        self.store.save_task(task)

        result = self.executor.resume(task.task_id)

        self.assertEqual(
            result.status,
            TaskStatus.COMPLETED,
        )
        self.assertEqual(
            result.steps[0].status,
            StepStatus.COMPLETED,
        )
        self.assertEqual(
            result.steps[0].output,
            "Content from documents/example.md",
        )

    def test_resume_rejects_completed_task(self):
        task = TaskPlan(
            description="Already completed",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_text",
                    arguments={"path": "documents/example.md"},
                    status=StepStatus.COMPLETED,
                    output="Existing content",
                )
            ],
            status=TaskStatus.COMPLETED,
        )

        self.store.save_task(task)

        with self.assertRaises(ValueError):
            self.executor.resume(task.task_id)

    def test_resume_missing_task_fails(self):
        with self.assertRaises(ValueError):
            self.executor.resume("missing-task-id")

    def test_resume_preserves_previous_step_outputs(self):
        def first():
            return "first-output"

        def second(value):
            return f"second received {value}"

        self.registry = ToolRegistry()

        self.registry.register(
            ToolDefinition(
                name="first",
                description="Return first output",
                handler=first,
                required_arguments=set(),
            )
        )

        self.registry.register(
            ToolDefinition(
                name="second",
                description="Consume first output",
                handler=second,
                required_arguments={"value"},
            )
        )

        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.store,
        )

        task = TaskPlan(
            description="resume with references",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="first",
                    arguments={},
                ),
                TaskStep(
                    step_id=2,
                    tool="second",
                    arguments={
                        "value": "$step_1",
                    },
                ),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(
            result.steps[0].output,
            "first-output",
        )
        self.assertEqual(
            result.steps[1].output,
            "second received first-output",
        )

        stored_task = self.store.get_task(task.task_id)

        stored_task.steps[1].status = StepStatus.RUNNING
        stored_task.status = TaskStatus.RUNNING
        self.store.save_task(stored_task)

        resumed = self.executor.resume(task.task_id)

        self.assertEqual(
            resumed.status,
            TaskStatus.COMPLETED,
        )
        self.assertEqual(
            resumed.steps[0].output,
            "first-output",
        )
        self.assertEqual(
            resumed.steps[1].output,
            "second received first-output",
        )

    def test_resume_does_not_rerun_completed_steps(self):
        call_counts = {
            "first": 0,
            "second": 0,
        }

        def first():
            call_counts["first"] += 1
            return "first-output"

        def second():
            call_counts["second"] += 1
            return "second-output"

        self.registry = ToolRegistry()

        self.registry.register(
            ToolDefinition(
                name="first",
                description="First tool",
                handler=first,
                required_arguments=set(),
            )
        )

        self.registry.register(
            ToolDefinition(
                name="second",
                description="Second tool",
                handler=second,
                required_arguments=set(),
            )
        )

        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.store,
        )

        task = TaskPlan(
            description="do not rerun completed work",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="first",
                    arguments={},
                ),
                TaskStep(
                    step_id=2,
                    tool="second",
                    arguments={},
                ),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(
            result.status,
            TaskStatus.COMPLETED,
        )
        self.assertEqual(
            call_counts["first"],
            1,
        )
        self.assertEqual(
            call_counts["second"],
            1,
        )

        stored_task = self.store.get_task(task.task_id)

        stored_task.steps[1].status = StepStatus.RUNNING
        stored_task.status = TaskStatus.RUNNING
        self.store.save_task(stored_task)

        resumed = self.executor.resume(task.task_id)

        self.assertEqual(
            resumed.status,
            TaskStatus.COMPLETED,
        )

        # Step 1 sudah completed → tidak boleh dijalankan lagi.
        self.assertEqual(
            call_counts["first"],
            1,
        )

        # Step 2 sebelumnya RUNNING → dianggap interrupted → dijalankan ulang.
        self.assertEqual(
            call_counts["second"],
            2,
        )


if __name__ == "__main__":
    unittest.main()