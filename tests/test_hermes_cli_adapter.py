import subprocess
import unittest
from unittest.mock import MagicMock, patch

from src.hermes.adapter import HermesCLIAdapter
from src.hermes.config import HermesConfig
from src.hermes.errors import (
    HermesExecutionError,
    HermesTimeoutError,
    HermesUnavailableError,
    InvalidRequestError,
)


class TestHermesCLIAdapter(unittest.TestCase):
    def setUp(self):
        self.config = HermesConfig(
            executable_path="/mock/bin/hermes",
            timeout=10,
            max_output_size=500,
            max_request_size=200,
        )
        self.adapter = HermesCLIAdapter(config=self.config)

    def test_disabled_adapter_raises_unavailable(self):
        disabled_config = HermesConfig(enabled=False)
        adapter = HermesCLIAdapter(config=disabled_config)
        with self.assertRaises(HermesUnavailableError) as ctx:
            adapter.invoke("Hello")
        self.assertIn("disabled", str(ctx.exception))

    def test_oversized_query_raises_invalid_request(self):
        with self.assertRaises(InvalidRequestError) as ctx:
            self.adapter.invoke("x" * 250)
        self.assertIn("exceeds maximum allowed length", str(ctx.exception))

    @patch("subprocess.run")
    def test_successful_invocation(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Hermes response output",
            stderr="",
        )

        output = self.adapter.invoke("Calculate 2+2")
        self.assertEqual(output, "Hermes response output")

        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][0], "/mock/bin/hermes")
        self.assertIn("-q", args[0])
        self.assertIn("Calculate 2+2", args[0])
        self.assertFalse(kwargs.get("shell", False))
        self.assertEqual(kwargs.get("timeout"), 10)

    @patch("subprocess.run")
    def test_executable_not_found_raises_unavailable(self, mock_run):
        mock_run.side_effect = FileNotFoundError("Executable not found")
        with self.assertRaises(HermesUnavailableError) as ctx:
            self.adapter.invoke("Test query")
        self.assertIn("Executable not found", str(ctx.exception))

    @patch("subprocess.run")
    def test_timeout_raises_timeout_error(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["hermes"], timeout=10)
        with self.assertRaises(HermesTimeoutError) as ctx:
            self.adapter.invoke("Test query")
        self.assertIn("timed out after 10 seconds", str(ctx.exception))

    @patch("subprocess.run")
    def test_nonzero_exit_code_raises_execution_error(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Failed to load model",
        )
        with self.assertRaises(HermesExecutionError) as ctx:
            self.adapter.invoke("Test query")
        self.assertIn("Failed to load model", str(ctx.exception))

    @patch("subprocess.run")
    def test_oversized_output_is_truncated(self, mock_run):
        huge_output = "A" * 1000
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=huge_output,
            stderr="",
        )
        output = self.adapter.invoke("Test query")
        self.assertLessEqual(len(output), 500 + len("\n... [TRUNCATED]"))
        self.assertTrue(output.endswith("[TRUNCATED]"))


if __name__ == "__main__":
    unittest.main()
