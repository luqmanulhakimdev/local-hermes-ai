import unittest
import time

from src.automation.executor import TaskExecutor
from src.automation.models import (
    TaskPlan,
    TaskStep,
    TaskStatus,
    StepStatus,
)
from src.automation.registry import ToolDefinition, ToolRegistry


class TestTaskExecutor(unittest.TestCase):

    def setUp(self):
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

        self.registry.register(
            ToolDefinition(
                name="save_note",
                description="Save a note",
                handler=lambda content: f"Saved: {content}",
                required_arguments={"content"},
            )
        )

        self.executor = TaskExecutor(self.registry)

    def test_execute_single_step(self):
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
        self.assertEqual(
            result.steps[0].status,
            StepStatus.COMPLETED,
        )
        self.assertEqual(
            result.steps[0].output,
            "Content from documents/example.md",
        )

    def test_execute_multiple_steps_with_reference(self):
        task = TaskPlan(
            description="Read and summarize a document",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_text",
                    arguments={"path": "documents/example.md"},
                ),
                TaskStep(
                    step_id=2,
                    tool="summarize",
                    arguments={"text": "$step_1"},
                ),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(
            result.steps[1].output,
            "Summary: Content from documents/example.md",
        )

    def test_nested_step_reference(self):
        value = {
            "content": ["$step_1"],
            "metadata": {"source": "example.md"},
        }

        resolved = self.executor._resolve_value(
            value,
            current_step_id=2,
            outputs={1: "Document content"},
        )

        self.assertEqual(
            resolved,
            {
                "content": ["Document content"],
                "metadata": {"source": "example.md"},
            },
        )

    def test_unknown_tool_fails_task(self):
        task = TaskPlan(
            description="Try an unknown tool",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="unknown_tool",
                )
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertIn("Tool is not allowed", result.steps[0].error)

    def test_execution_stops_after_failure(self):
        task = TaskPlan(
            description="Stop after a failed step",
            steps=[
                TaskStep(step_id=1, tool="unknown_tool"),
                TaskStep(
                    step_id=2,
                    tool="read_text",
                    arguments={"path": "example.md"},
                ),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertEqual(result.steps[1].status, StepStatus.PENDING)

    def test_current_step_reference_is_rejected(self):
        task = TaskPlan(
            description="Invalid self reference",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="summarize",
                    arguments={"text": "$step_1"},
                )
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertIn(
            "previous steps",
            result.steps[0].error,
        )

    def test_failed_handler_is_recorded(self):
        def failing_tool():
            raise RuntimeError("Something went wrong")

        self.registry.register(
            ToolDefinition(
                name="failing_tool",
                description="Always fails",
                handler=failing_tool,
                required_arguments=set(),
            )
        )

        task = TaskPlan(
            description="Test handler failure",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="failing_tool",
                )
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertIn("RuntimeError", result.steps[0].error)

    def test_completed_task_cannot_be_executed_again(self):
        task = TaskPlan(
            description="Read a document",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_text",
                    arguments={"path": "example.md"},
                )
            ],
        )

        self.executor.execute(task)

        with self.assertRaises(ValueError):
            self.executor.execute(task)

    def test_output_within_limit_is_accepted(self):
        executor = TaskExecutor(
            self.registry,
            max_output_size=100,
        )

        task = TaskPlan(
            description="Small output",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_text",
                    arguments={"path": "example.md"},
                )
            ],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.steps[0].status, StepStatus.COMPLETED)

    def test_output_exceeding_limit_fails_task(self):
        executor = TaskExecutor(
            self.registry,
            max_output_size=10,
        )

        task = TaskPlan(
            description="Large output",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_text",
                    arguments={"path": "example.md"},
                )
            ],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertIn(
            "exceeds maximum allowed size",
            result.steps[0].error,
        )

    def test_invalid_output_limit_rejected(self):
        with self.assertRaises(ValueError):
            TaskExecutor(
                self.registry,
                max_output_size=0,
            )

    def test_tool_timeout_fails_task(self):
        def slow_tool():
            time.sleep(2)
            return "finished"

        self.registry.register(
            ToolDefinition(
                name="slow_tool",
                description="Slow tool",
                handler=slow_tool,
                required_arguments=set(),
            )
        )

        executor = TaskExecutor(
            self.registry,
            tool_timeout=1,
        )

        task = TaskPlan(
            description="Test timeout",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="slow_tool",
                )
            ],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertIn(
            "Tool execution exceeded",
            result.steps[0].error,
        )
    
    def test_invalid_tool_timeout_rejected(self):
        with self.assertRaises(ValueError):
            TaskExecutor(
                self.registry,
                tool_timeout=0,
            )

    def test_steps_after_failure_remain_pending(self):
        def failing_tool():
            raise RuntimeError("Simulated failure")

        self.registry.register(
            ToolDefinition(
                name="failing_tool",
                description="A tool that fails",
                handler=failing_tool,
                required_arguments=set(),
            )
        )

        task = TaskPlan(
            description="Test state consistency",
            steps=[
                TaskStep(step_id=1, tool="failing_tool"),
                TaskStep(
                    step_id=2,
                    tool="greet",
                    arguments={"name": "Hermes"},
                ),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertEqual(result.steps[1].status, StepStatus.PENDING)

        self.assertIsNotNone(result.steps[0].error)
        self.assertIsNone(result.steps[1].error)
        self.assertIsNone(result.steps[1].output)


    def test_failed_step_does_not_store_output(self):
        def failing_tool():
            raise RuntimeError("Tool failed")

        self.registry.register(
            ToolDefinition(
                name="failing_tool",
                description="A tool that fails",
                handler=failing_tool,
                required_arguments=set(),
            )
        )

        task = TaskPlan(
            description="Test failed output",
            steps=[
                TaskStep(step_id=1, tool="failing_tool"),
            ],
        )

        result = self.executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertIsNone(result.steps[0].output)
        self.assertIsNotNone(result.steps[0].error)


if __name__ == "__main__":
    unittest.main()
