import io
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import src.agent as agent_module


class TestAgent(unittest.TestCase):
    def setUp(self):
        # Reset conversation history before each test
        agent_module.messages.clear()
        agent_module.messages.append({
            "role": "system",
            "content": agent_module.SYSTEM_PROMPT
        })

    @patch("requests.post")
    def test_ask_ai_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "content": "I am doing well, thank you!"
            }
        }
        mock_post.return_value = mock_response

        answer = agent_module.ask_ai("How are you?")

        self.assertEqual(answer, "I am doing well, thank you!")
        self.assertEqual(len(agent_module.messages), 3)
        self.assertEqual(agent_module.messages[1], {"role": "user", "content": "How are you?"})
        self.assertEqual(
            agent_module.messages[2],
            {"role": "assistant", "content": "I am doing well, thank you!"}
        )

        mock_post.assert_called_once_with(
            agent_module.OLLAMA_URL,
            json={
                "model": agent_module.MODEL,
                "messages": agent_module.messages,
                "stream": False,
            },
            timeout=(10, 300),
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("requests.post", side_effect=requests.exceptions.RequestException("Network down"))
    def test_ask_ai_raises_request_exception(self, mock_post):
        with self.assertRaises(requests.exceptions.RequestException):
            agent_module.ask_ai("Hello")

    @patch("src.agent.ask_ai", return_value="Here is your answer.")
    @patch("builtins.input", side_effect=["Luqman", "What is AI?", "exit"])
    def test_main_normal_flow_and_exit(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            agent_module.main()

            output = mock_stdout.getvalue()
            self.assertIn("Hello Luqman! Nice to meet you.", output)
            self.assertIn("AI: Here is your answer.", output)
            self.assertIn("AI: Goodbye!", output)
            mock_ask_ai.assert_called_once_with("What is AI?")

    @patch("builtins.input", side_effect=["", "exit"])
    def test_main_empty_name_defaults_to_friend(self, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            agent_module.main()

            output = mock_stdout.getvalue()
            self.assertIn("Hello Friend! Nice to meet you.", output)

    @patch("builtins.input", side_effect=["Alice", "reset", "exit"])
    def test_main_reset_command(self, mock_input):
        # Add some dummy messages
        agent_module.messages.append({"role": "user", "content": "Old message"})

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            agent_module.main()

            output = mock_stdout.getvalue()
            self.assertIn("AI: Conversation history has been reset.", output)
            self.assertEqual(len(agent_module.messages), 1)
            self.assertEqual(agent_module.messages[0]["role"], "system")

    @patch("builtins.input", side_effect=["Alice", "   ", "exit"])
    def test_main_empty_question_skipped(self, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            with patch("src.agent.ask_ai") as mock_ask_ai:
                agent_module.main()
                mock_ask_ai.assert_not_called()

    @patch("src.agent.ask_ai")
    @patch("builtins.input", side_effect=["Alice", "Hello", "exit"])
    def test_main_request_exception_handling(self, mock_input, mock_ask_ai):
        def raise_conn_error(q):
            agent_module.messages.append({"role": "user", "content": q})
            raise requests.exceptions.RequestException("Connection refused")

        mock_ask_ai.side_effect = raise_conn_error

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            agent_module.main()

            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] Could not connect to Ollama: Connection refused", output)
            # The failed user message should have been popped
            self.assertEqual(len(agent_module.messages), 1)
            self.assertEqual(agent_module.messages[0]["role"], "system")

    @patch("src.agent.ask_ai", side_effect=KeyError("message"))
    @patch("builtins.input", side_effect=["Alice", "Hello", "exit"])
    def test_main_invalid_response_handling(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            agent_module.main()

            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] Invalid Ollama response: 'message'", output)


if __name__ == "__main__":
    unittest.main()

