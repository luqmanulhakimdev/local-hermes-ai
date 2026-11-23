import tempfile
import unittest
from pathlib import Path

from src.automation.executor import TaskExecutor
from src.automation.models import TaskPlan, TaskStep
from src.automation.planner import MAX_PLANNER_REQUEST_SIZE, TaskPlanner
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore
from src.automation.validator import TaskValidator
from src.automation_agent import AutomationAgent


class TestResourceLimits(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.registry = ToolRegistry()
        self.task_store = TaskStore(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_huge_tool_output_exceeds_limit(self):
        self.registry.register(
            ToolDefinition(
                name="generate_huge",
                description="Generates huge output",
                handler=lambda: "x" * 25_000,
                required_arguments=set(),
            )
        )
        executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            max_output_size=20_000,
        )
        task = TaskPlan(
            description="Test output limit",
            steps=[TaskStep(step_id=1, tool="generate_huge")],
        )

        result = executor.execute(task)

        self.assertEqual(result.status.value, "failed")
        self.assertIn("exceeds maximum allowed size", result.steps[0].error)

    def test_planner_request_size_limit(self):
        planner = TaskPlanner()
        huge_request = "a" * (MAX_PLANNER_REQUEST_SIZE + 1)
        with self.assertRaises(ValueError) as ctx:
            planner.plan(huge_request)
        self.assertIn("exceeds maximum allowed length", str(ctx.exception))

    def test_agent_request_size_limit(self):
        agent = AutomationAgent()
        huge_request = "b" * (MAX_PLANNER_REQUEST_SIZE + 1)
        with self.assertRaises(ValueError) as ctx:
            agent.run(huge_request)
        self.assertIn("exceeds maximum allowed length", str(ctx.exception))

    def test_excessive_task_steps_rejected_by_model_and_validator(self):
        # TaskPlan already enforces MAX_TASK_STEPS = 5
        steps = [
            TaskStep(step_id=i, tool="tool")
            for i in range(1, 7)
        ]
        with self.assertRaises(ValueError) as ctx:
            TaskPlan(description="Too many steps", steps=steps)
        self.assertIn("cannot contain more than 5 steps", str(ctx.exception))

    def test_deeply_nested_arguments_rejected(self):
        validator = TaskValidator(self.registry)
        self.registry.register(
            ToolDefinition(
                name="nested_tool",
                description="Nested tool",
                handler=lambda payload: "ok",
                required_arguments={"payload"},
            )
        )

        # Build deeply nested dictionary (> 10 levels)
        nested = {"level": 1}
        cur = nested
        for i in range(2, 15):
            cur["inner"] = {"level": i}
            cur = cur["inner"]

        task = TaskPlan(
            description="Deep nesting test",
            steps=[TaskStep(step_id=1, tool="nested_tool", arguments={"payload": nested})],
        )

        with self.assertRaises(ValueError) as ctx:
            validator.validate(task)
        self.assertIn("Argument nesting exceeds maximum allowed depth", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
