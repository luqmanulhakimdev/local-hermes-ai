import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.memory import Memory
import src.personal_agent as personal_agent_module


class TestPersonalAgent(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_db = Path(self.temp_dir.name) / "test_personal_agent.db"
        self.test_memory = Memory(db_path=self.test_db)
        self.original_memory = personal_agent_module.memory
        personal_agent_module.memory = self.test_memory

    def tearDown(self):
        personal_agent_module.memory = self.original_memory
        try:
            self.test_memory.close()
        except Exception:
            pass
        self.temp_dir.cleanup()

    def test_execute_tool_unknown(self):
        result = personal_agent_module.execute_tool("unknown_tool", {})
        self.assertEqual(result, {"error": "Unknown tool."})

    def test_execute_tool_calculate(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            result = personal_agent_module.execute_tool("calculate", {"expression": "5 * 6"})
            self.assertEqual(result, {"result": 30})

    def test_execute_tool_calculate_error(self):
        result = personal_agent_module.execute_tool("calculate", {"expression": "invalid &^%"})
        self.assertIn("error", result)

    def test_execute_tool_get_current_time(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            result = personal_agent_module.execute_tool("get_current_time", {})
            self.assertIn("result", result)
            self.assertIn("timezone", result["result"])

    def test_execute_tool_list_project_files(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            result = personal_agent_module.execute_tool("list_project_files", {})
            self.assertIn("result", result)
            self.assertIsInstance(result["result"], list)

    def test_execute_tool_read_project_file(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            result = personal_agent_module.execute_tool(
                "read_project_file",
                {"filename": "requirements.txt"}
            )
            self.assertIn("result", result)

    def test_execute_tool_read_project_file_not_found(self):
        result = personal_agent_module.execute_tool(
            "read_project_file",
            {"filename": "missing_file_xyz.txt"}
        )
        self.assertEqual(result, {"error": "File not found."})

    def test_build_messages(self):
        self.test_memory.remember("user_role", "developer")
        self.test_memory.save_message("user", "Hello agent")

        messages = personal_agent_module.build_messages()
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("developer", messages[0]["content"])
        self.assertEqual(messages[1], {"role": "user", "content": "Hello agent"})

    @patch("requests.post")
    def test_ask_ai_direct_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "No tools needed, here is the answer."
            }
        }
        mock_post.return_value = mock_response

        answer = personal_agent_module.ask_ai("What is 1 + 1?")
        self.assertEqual(answer, "No tools needed, here is the answer.")

        # Ensure saved to memory
        recent = self.test_memory.get_recent_messages()
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["role"], "user")
        self.assertEqual(recent[1]["content"], "No tools needed, here is the answer.")

    @patch("requests.post")
    def test_ask_ai_with_tool_call_flow(self, mock_post):
        tool_call_resp = MagicMock()
        tool_call_resp.json.return_value = {
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "calculate",
                            "arguments": {"expression": "12 * 12"}
                        }
                    }
                ]
            }
        }

        final_resp = MagicMock()
        final_resp.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "12 multiplied by 12 is 144."
            }
        }

        mock_post.side_effect = [tool_call_resp, final_resp]

        with patch("sys.stdout", new_callable=io.StringIO):
            answer = personal_agent_module.ask_ai("Calculate 12 * 12")

        self.assertEqual(answer, "12 multiplied by 12 is 144.")
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.post")
    def test_ask_ai_exceeds_tool_limit(self, mock_post):
        tool_call_resp = MagicMock()
        tool_call_resp.json.return_value = {
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_current_time",
                            "arguments": {}
                        }
                    }
                ]
            }
        }
        mock_post.return_value = tool_call_resp

        with patch("sys.stdout", new_callable=io.StringIO):
            answer = personal_agent_module.ask_ai("Keep calling tools")

        self.assertEqual(
            answer,
            "Tool usage limit reached. Please try a simpler instruction."
        )

    @patch("builtins.input", side_effect=["/exit"])
    def test_main_exit(self, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            personal_agent_module.main()
            self.assertIn("AI: Goodbye!", mock_stdout.getvalue())

    @patch("builtins.input", side_effect=["/memories", "/exit"])
    def test_main_memories(self, mock_input):
        self.test_memory.remember("pet", "cat")
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            personal_agent_module.main()
            output = mock_stdout.getvalue()
            self.assertIn('"pet": "cat"', output)

    @patch("src.personal_agent.ask_ai")
    @patch("builtins.input", side_effect=[
        "/remember",
        "/remember invalid_format",
        "/remember empty_val=",
        "/remember city=Bandung",
        "/exit"
    ])
    def test_main_remember_commands(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            personal_agent_module.main()
            output = mock_stdout.getvalue()
            self.assertIn("Format: /remember key=value", output)
            self.assertIn("Key and value cannot be empty.", output)
            self.assertIn("AI: Information saved successfully.", output)

            verify_memory = Memory(db_path=self.test_db)
            self.assertEqual(verify_memory.get_memories().get("city"), "Bandung")
            verify_memory.close()
            mock_ask_ai.assert_not_called()

    @patch("src.personal_agent.ask_ai")
    @patch("builtins.input", side_effect=[
        "/forget",
        "/forget city",
        "/remember city=Jakarta",
        "/forget city",
        "/exit"
    ])
    def test_main_forget_command(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            personal_agent_module.main()
            output = mock_stdout.getvalue()
            self.assertIn("Format: /forget key", output)
            self.assertIn("AI: Information not found.", output)
            self.assertIn("AI: Information deleted successfully.", output)
            mock_ask_ai.assert_not_called()

    @patch("src.personal_agent.ask_ai")
    @patch("builtins.input", side_effect=["/reset", "/exit"])
    def test_main_reset_command(self, mock_input, mock_ask_ai):
        self.test_memory.save_message("user", "Hello")
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            personal_agent_module.main()
            output = mock_stdout.getvalue()
            self.assertIn("AI: Conversation history cleared.", output)

            verify_memory = Memory(db_path=self.test_db)
            self.assertEqual(verify_memory.get_recent_messages(), [])
            verify_memory.close()
            mock_ask_ai.assert_not_called()

    @patch("builtins.input", side_effect=["   ", "What is AI?", "/exit"])
    @patch("src.personal_agent.ask_ai", return_value="AI is Artificial Intelligence.")
    def test_main_prompt_and_empty_skip(self, mock_ask_ai, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            personal_agent_module.main()
            output = mock_stdout.getvalue()
            self.assertIn("AI: AI is Artificial Intelligence.", output)
            mock_ask_ai.assert_called_once_with("What is AI?")

    @patch("builtins.input", side_effect=["Question", "/exit"])
    @patch("src.personal_agent.ask_ai", side_effect=requests.exceptions.RequestException("Conn error"))
    def test_main_request_exception(self, mock_ask_ai, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            personal_agent_module.main()
            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] Could not connect to Ollama: Conn error", output)

    @patch("builtins.input", side_effect=["Question", "/exit"])
    @patch("src.personal_agent.ask_ai", side_effect=ValueError("Bad tool data"))
    def test_main_value_error(self, mock_ask_ai, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            personal_agent_module.main()
            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] Invalid response or tool data: Bad tool data", output)


if __name__ == "__main__":
    unittest.main()
