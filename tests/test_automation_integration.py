
import tempfile
import unittest
from pathlib import Path

from src.automation_agent import AutomationAgent
from src.automation.models import (
    TaskPlan,
    TaskStep,
    TaskStatus,
    StepStatus,
)
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.logger import TaskLogger
from src.tools.file_tools import read_file


class MockPlanner:
    def __init__(self, task):
        self.task = task
        self.received_request = None

    def plan(self, user_request):
        self.received_request = user_request
        return self.task


class TestAutomationIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.logger = TaskLogger(
            db_path=Path(self.temp_dir.name) / "test_logs.db"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_registry(self):
        registry = ToolRegistry()

        registry.register(
            ToolDefinition(
                "get_text",
                "Return sample text",
                lambda: "Hello from integration test",
                set(),
            )
        )

        registry.register(
            ToolDefinition(
                "uppercase",
                "Convert text to uppercase",
                lambda text: text.upper(),
                {"text"},
            )
        )

        return registry

    def test_successful_multi_step_workflow(self):
        registry = self.create_registry()

        task = TaskPlan(
            description="Get text and convert it to uppercase",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="get_text",
                    arguments={},
                ),
                TaskStep(
                    step_id=2,
                    tool="uppercase",
                    arguments={"text": "$step_1"},
                ),
            ],
        )

        planner = MockPlanner(task)

        agent = AutomationAgent(
            planner=planner,
            registry=registry,
            logger=self.logger,
        )

        result = agent.run("Convert sample text to uppercase")

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(
            result.steps[0].output,
            "Hello from integration test",
        )
        self.assertEqual(
            result.steps[1].output,
            "HELLO FROM INTEGRATION TEST",
        )
        self.assertEqual(
            planner.received_request,
            "Convert sample text to uppercase",
        )

        logs = self.logger.get_task_logs(result.task_id)
        events = [log["event"] for log in logs]

        self.assertIn("task_started", events)
        self.assertIn("step_completed", events)
        self.assertIn("task_completed", events)

    def test_unknown_tool_is_rejected_before_execution(self):
        executed = []

        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                "safe_tool",
                "A safe test tool",
                lambda: executed.append(True),
                set(),
            )
        )

        task = TaskPlan(
            description="Attempt to execute an unknown tool",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="dangerous_tool",
                    arguments={},
                ),
            ],
        )

        agent = AutomationAgent(
            planner=MockPlanner(task),
            registry=registry,
            logger=self.logger,
        )

        result = agent.run("Run an unknown tool")

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertEqual(executed, [])

    def test_execution_stops_after_tool_failure(self):
        executed = []

        registry = ToolRegistry()

        def failing_tool():
            raise RuntimeError("Simulated tool failure")

        def later_tool():
            executed.append("later")
            return "Should not execute"

        registry.register(
            ToolDefinition(
                "failing_tool",
                "A tool that fails",
                failing_tool,
                set(),
            )
        )

        registry.register(
            ToolDefinition(
                "later_tool",
                "A tool that should not run",
                later_tool,
                set(),
            )
        )

        task = TaskPlan(
            description="Test execution failure",
            steps=[
                TaskStep(1, "failing_tool", {}),
                TaskStep(2, "later_tool", {}),
            ],
        )

        agent = AutomationAgent(
            planner=MockPlanner(task),
            registry=registry,
            logger=self.logger,
        )

        result = agent.run("Run a failing workflow")

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertEqual(result.steps[1].status, StepStatus.PENDING)
        self.assertEqual(executed, [])

        logs = self.logger.get_task_logs(result.task_id)
        events = [log["event"] for log in logs]

        self.assertIn("step_failed", events)
        self.assertIn("task_failed", events)
        self.assertNotIn("task_completed", events)

    def test_path_traversal_is_rejected(self):
        registry = ToolRegistry()

        registry.register(
            ToolDefinition(
                "read_file",
                "Read an allowed document",
                read_file,
                {"path"},
            )
        )

        task = TaskPlan(
            description="Attempt to read outside documents",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_file",
                    arguments={"path": "../../README.md"},
                ),
            ],
        )

        agent = AutomationAgent(
            planner=MockPlanner(task),
            registry=registry,
            logger=self.logger,
        )

        result = agent.run("Read a file outside the documents directory")

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertIn(
            "restricted to documents",
            result.steps[0].error,
        )


if __name__ == "__main__":
    unittest.main()
