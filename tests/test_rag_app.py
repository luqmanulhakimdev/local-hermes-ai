import io
import unittest
from unittest.mock import patch

from src.rag.app import main


class TestRAGApp(unittest.TestCase):

    @patch("builtins.input", side_effect=["exit"])
    def test_main_exit(self, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            self.assertIn("LOCAL RAG ASSISTANT", output)
            self.assertIn("Assistant: Goodbye!", output)

    @patch("builtins.input", side_effect=["quit"])
    def test_main_quit(self, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            self.assertIn("Assistant: Goodbye!", output)

    @patch("builtins.input", side_effect=["help", "exit"])
    def test_main_help(self, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            self.assertIn("Commands:", output)
            self.assertIn("help  - Show help instructions", output)

    @patch("src.rag.app.answer_question", return_value="An AI agent uses tools.")
    @patch("builtins.input", side_effect=["", "What is an agent?", "exit"])
    def test_main_ask_question(self, mock_input, mock_answer):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            self.assertIn("Assistant: Searching for answers...", output)
            self.assertIn("An AI agent uses tools.", output)
            mock_answer.assert_called_once_with("What is an agent?", top_k=3)

    @patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_main_keyboard_interrupt(self, mock_input):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            self.assertIn("Assistant: Goodbye!", output)

    @patch("src.rag.app.answer_question", side_effect=ValueError("Test error"))
    @patch("builtins.input", side_effect=["trigger error", "exit"])
    def test_main_error_handling(self, mock_input, mock_answer):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            main()
            output = mock_stdout.getvalue()
            self.assertIn("Error: Test error", output)


if __name__ == "__main__":
    unittest.main()

