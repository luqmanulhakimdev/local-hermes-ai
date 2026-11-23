import json
import unittest
from unittest.mock import MagicMock, patch

from src.automation.planner import TaskPlanner
from src.automation.registry import ToolDefinition, ToolRegistry


class TestPlannerHardening(unittest.TestCase):
    def setUp(self):
        self.planner = TaskPlanner()

    def _mock_response(self, content_dict_or_str):
        mock_resp = MagicMock()
        if isinstance(content_dict_or_str, (dict, list)):
            content = json.dumps(content_dict_or_str)
        else:
            content = str(content_dict_or_str)
        mock_resp.json.return_value = {
            "message": {
                "content": content
            }
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @patch("requests.post")
    def test_malformed_json_response_rejected(self, mock_post):
        mock_post.return_value = self._mock_response("Not valid JSON at all {")
        with self.assertRaises(ValueError) as ctx:
            self.planner.plan("do something")
        self.assertIn("invalid JSON", str(ctx.exception))

    @patch("requests.post")
    def test_unexpected_root_fields_rejected(self, mock_post):
        payload = {
            "description": "Task",
            "steps": [{"step_id": 1, "tool": "read_file", "arguments": {"path": "a"}}],
            "injected_field": "exploit",
        }
        mock_post.return_value = self._mock_response(payload)
        with self.assertRaises(ValueError) as ctx:
            self.planner.plan("do something")
        self.assertIn("contain only description and steps", str(ctx.exception))

    @patch("requests.post")
    def test_unexpected_step_fields_rejected(self, mock_post):
        payload = {
            "description": "Task",
            "steps": [
                {
                    "step_id": 1,
                    "tool": "read_file",
                    "arguments": {"path": "a"},
                    "extra_field": "dangerous",
                }
            ],
        }
        mock_post.return_value = self._mock_response(payload)
        with self.assertRaises(ValueError) as ctx:
            self.planner.plan("do something")
        self.assertIn("Invalid step structure", str(ctx.exception))

    @patch("requests.post")
    def test_empty_tool_name_rejected(self, mock_post):
        payload = {
            "description": "Task",
            "steps": [{"step_id": 1, "tool": "", "arguments": {}}],
        }
        mock_post.return_value = self._mock_response(payload)
        with self.assertRaises(ValueError) as ctx:
            self.planner.plan("do something")
        self.assertIn("tool", str(ctx.exception).lower())

    @patch("requests.post")
    def test_non_dict_arguments_rejected(self, mock_post):
        payload = {
            "description": "Task",
            "steps": [{"step_id": 1, "tool": "read_file", "arguments": ["not_a_dict"]}],
        }
        mock_post.return_value = self._mock_response(payload)
        with self.assertRaises(ValueError) as ctx:
            self.planner.plan("do something")
        self.assertIn("arguments must be a JSON object", str(ctx.exception))

    @patch("requests.post")
    def test_invalid_step_ids_rejected(self, mock_post):
        # Step ID starting from 0
        payload = {
            "description": "Task",
            "steps": [{"step_id": 0, "tool": "read_file", "arguments": {"path": "a"}}],
        }
        mock_post.return_value = self._mock_response(payload)
        with self.assertRaises(ValueError):
            self.planner.plan("do something")

        # Non-sequential step IDs
        payload = {
            "description": "Task",
            "steps": [
                {"step_id": 1, "tool": "read_file", "arguments": {"path": "a"}},
                {"step_id": 3, "tool": "read_file", "arguments": {"path": "b"}},
            ],
        }
        mock_post.return_value = self._mock_response(payload)
        with self.assertRaises(ValueError):
            self.planner.plan("do something")

    @patch("requests.post")
    def test_allowed_tools_enforcement_when_registry_provided(self, mock_post):
        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                name="allowed_tool",
                description="desc",
                handler=lambda: "ok",
                required_arguments=set(),
            )
        )
        planner = TaskPlanner(registry=registry)

        payload = {
            "description": "Task with unauthorized tool",
            "steps": [{"step_id": 1, "tool": "evil_tool", "arguments": {}}],
        }
        mock_post.return_value = self._mock_response(payload)

        with self.assertRaises(ValueError) as ctx:
            planner.plan("do something")
        self.assertIn("evil_tool", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
