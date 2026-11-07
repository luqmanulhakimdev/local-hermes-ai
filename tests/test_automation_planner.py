
import unittest
from unittest.mock import Mock, patch

from src.automation.planner import TaskPlanner


class TestTaskPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = TaskPlanner()

    @patch("src.automation.planner.requests.post")
    def test_create_valid_plan(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "content": """
                {
                    "description": "Read and summarize a document",
                    "steps": [
                        {
                            "step_id": 1,
                            "tool": "read_file",
                            "arguments": {
                                "path": "documents/ai-engineering.md"
                            }
                        },
                        {
                            "step_id": 2,
                            "tool": "summarize_text",
                            "arguments": {
                                "text": "$step_1"
                            }
                        }
                    ]
                }
                """
            }
        }

        mock_post.return_value = mock_response

        task = self.planner.plan("Read and summarize ai-engineering.md")

        self.assertEqual(task.description, "Read and summarize a document")
        self.assertEqual(len(task.steps), 2)
        self.assertEqual(task.steps[0].tool, "read_file")
        self.assertEqual(task.steps[1].arguments["text"], "$step_1")

        mock_post.assert_called_once()

    def test_empty_request_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            self.planner.plan(" ")

    @patch("src.automation.planner.requests.post")
    def test_invalid_json_is_rejected(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "not valid json"}
        }
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            self.planner.plan("Read a document")

    @patch("src.automation.planner.requests.post")
    def test_planner_error_is_rejected(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "content": '{"error": "Unsupported request"}'
            }
        }
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(ValueError, "Unsupported request"):
            self.planner.plan("Do something unsupported")

    @patch("src.automation.planner.requests.post")
    def test_invalid_plan_structure_is_rejected(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "content": '{"description": "Missing steps"}'
            }
        }
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(ValueError, "only description and steps"):
            self.planner.plan("Read a document")

    @patch("src.automation.planner.requests.post")
    def test_more_than_five_steps_is_rejected(self, mock_post):
        steps = [
            {
                "step_id": i,
                "tool": "get_current_time",
                "arguments": {},
            }
            for i in range(1, 7)
        ]

        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {
                "content": __import__("json").dumps({
                    "description": "Too many steps",
                    "steps": steps,
                })
            }
        }
        mock_post.return_value = mock_response

        with self.assertRaisesRegex(ValueError, "more than 5"):
            self.planner.plan("Create a long task")

    @patch("src.automation.planner.requests.post")
    def test_http_error_is_propagated(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = (
            __import__("requests").exceptions.ConnectionError("Ollama unavailable")
        )
        mock_post.return_value = mock_response

        with self.assertRaises(
            __import__("requests").exceptions.ConnectionError
        ):
            self.planner.plan("Read a document")


if __name__ == "__main__":
    unittest.main()
