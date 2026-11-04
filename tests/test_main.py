import io
import json
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import requests

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.main import OLLAMA_URL, MODEL, ask_ai, main


class TestAskAi(unittest.TestCase):
    @patch("requests.post")
    def test_ask_ai_successful_streaming(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            json.dumps({"message": {"content": "Hello"}}).encode("utf-8"),
            b"",  # Empty line should be skipped
            json.dumps({"message": {"content": ", how can I help you today?"}}).encode("utf-8"),
        ]
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_post.return_value = mock_response

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            ask_ai("Hello")

            mock_post.assert_called_once_with(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": "/no_think\nHello",
                        }
                    ],
                    "stream": True,
                },
                stream=True,
                timeout=(10, 300),
            )
            mock_response.raise_for_status.assert_called_once()

            output = mock_stdout.getvalue()
            self.assertIn("AI: ", output)
            self.assertIn("Hello, how can I help you today?", output)

    @patch("requests.post")
    def test_ask_ai_with_missing_message_or_content(self, mock_post):
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            json.dumps({}).encode("utf-8"),
            json.dumps({"message": {}}).encode("utf-8"),
            json.dumps({"message": {"content": "Done"}}).encode("utf-8"),
        ]
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_post.return_value = mock_response

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            ask_ai("Test")
            output = mock_stdout.getvalue()
            self.assertIn("Done", output)

    @patch("requests.post")
    def test_ask_ai_raises_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_post.return_value = mock_response

        with patch("sys.stdout", new_callable=io.StringIO):
            with self.assertRaises(requests.exceptions.HTTPError):
                ask_ai("Question")


class TestMain(unittest.TestCase):
    @patch("src.main.ask_ai")
    @patch("builtins.input", side_effect=["Luqman", "How are you?"])
    def test_main_success_flow(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()

            mock_ask_ai.assert_called_once_with("How are you?")
            output = mock_stdout.getvalue()
            self.assertIn("Hello, Luqman! Welcome to Local Hermes AI.", output)

    @patch("src.main.ask_ai")
    @patch("builtins.input", side_effect=["   ", "New question"])
    def test_main_empty_name_defaults_to_user(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()

            mock_ask_ai.assert_called_once_with("New question")
            output = mock_stdout.getvalue()
            self.assertIn("Hello, User! Welcome to Local Hermes AI.", output)

    @patch("src.main.ask_ai")
    @patch("builtins.input", side_effect=["Luqman", "   "])
    def test_main_empty_question_aborts(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()

            mock_ask_ai.assert_not_called()
            output = mock_stdout.getvalue()
            self.assertIn("You have not entered a question.", output)

    @patch("src.main.ask_ai", side_effect=requests.exceptions.ConnectionError("Connection refused"))
    @patch("builtins.input", side_effect=["Luqman", "Test"])
    def test_main_connection_error(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()

            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] Could not connect to Ollama.", output)
            self.assertIn("sudo systemctl start ollama", output)

    @patch("src.main.ask_ai", side_effect=requests.exceptions.Timeout("Request timed out"))
    @patch("builtins.input", side_effect=["Luqman", "Test"])
    def test_main_timeout_error(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()

            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] Request to Ollama timed out.", output)

    @patch("src.main.ask_ai", side_effect=requests.exceptions.HTTPError("500 Internal Server Error"))
    @patch("builtins.input", side_effect=["Luqman", "Test"])
    def test_main_http_error(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()

            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] HTTP Error: 500 Internal Server Error", output)

    @patch("src.main.ask_ai", side_effect=requests.exceptions.RequestException("General request error"))
    @patch("builtins.input", side_effect=["Luqman", "Test"])
    def test_main_request_exception(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()

            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] Connection error: General request error", output)

    @patch("src.main.ask_ai", side_effect=Exception("Unexpected crash"))
    @patch("builtins.input", side_effect=["Luqman", "Test"])
    def test_main_generic_exception(self, mock_input, mock_ask_ai):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()

            output = mock_stdout.getvalue()
            self.assertIn("[ERROR] An error occurred: Unexpected crash", output)


if __name__ == "__main__":
    unittest.main()
