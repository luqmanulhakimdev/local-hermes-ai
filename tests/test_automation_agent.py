import unittest
from unittest.mock import Mock

from src.automation_agent import AutomationAgent
from src.automation.models import (
    TaskPlan,
    TaskStep,
    TaskStatus,
)


class TestAutomationAgent(unittest.TestCase):
    def setUp(self):
        self.task = TaskPlan(
            description="Test automation",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="test_tool",
                    arguments={},
                )
            ],
        )

        self.planner = Mock()
        self.planner.plan.return_value = self.task

        self.registry = Mock()
        self.logger = Mock()

        self.agent = AutomationAgent(
            planner=self.planner,
            registry=self.registry,
            logger=self.logger,
        )

    def test_run_calls_planner(self):
        self.agent.run("Run a test")

        self.planner.plan.assert_called_once_with("Run a test")

    def test_run_executes_task(self):
        result = self.agent.run("Run a test")

        self.assertEqual(result.status, TaskStatus.COMPLETED)

    def test_empty_request_rejected(self):
        with self.assertRaises(ValueError):
            self.agent.run("")

        self.planner.plan.assert_not_called()

    def test_whitespace_request_rejected(self):
        with self.assertRaises(ValueError):
            self.agent.run("   ")

    def test_planner_error_propagated(self):
        self.planner.plan.side_effect = ValueError(
            "Planner returned invalid JSON"
        )

        with self.assertRaises(ValueError):
            self.agent.run("Run a test")


if __name__ == "__main__":
    unittest.main()