import unittest

from src.automation.planner import TaskPlanner
from src.automation.tool_setup import create_tool_registry


class TestAutomationToolConsistency(unittest.TestCase):
    def setUp(self):
        self.planner = TaskPlanner()
        self.registry = create_tool_registry()

    def test_planner_tools_match_registry(self):
        prompt = self.planner._build_prompt("Test request")

        for tool_name in self.registry.list_tools():
            with self.subTest(tool=tool_name):
                self.assertIn(tool_name, prompt)

    def test_planner_does_not_reference_unregistered_tools(self):
        prompt = self.planner._build_prompt("Test request")

        unsupported_tools = [
            "calculator",
            "get_current_time",
        ]

        for tool_name in unsupported_tools:
            with self.subTest(tool=tool_name):
                self.assertNotIn(tool_name, prompt)


if __name__ == "__main__":
    unittest.main()