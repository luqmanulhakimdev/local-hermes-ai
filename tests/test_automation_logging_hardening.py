import tempfile
import unittest
from pathlib import Path

from src.automation.logger import TaskLogger


class TestLoggingHardening(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.logger = TaskLogger(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sensitive_argument_redaction(self):
        self.logger.log_event(
            task_id="t1",
            event="tool_called",
            step_id=1,
            details={
                "tool": "api_client",
                "arguments": {
                    "api_key": "super_secret_key_123",
                    "user_password": "my_password",
                    "auth_token": "bearer xyz",
                    "query": "safe query",
                },
            },
        )
        logs = self.logger.get_task_logs("t1")
        self.assertEqual(len(logs), 1)
        args = logs[0]["details"]["arguments"]
        self.assertEqual(args["api_key"], "[REDACTED]")
        self.assertEqual(args["user_password"], "[REDACTED]")
        self.assertEqual(args["auth_token"], "[REDACTED]")
        self.assertEqual(args["query"], "safe query")

    def test_oversized_payload_truncation(self):
        huge_str = "x" * 15_000
        self.logger.log_event(
            task_id="t2",
            event="step_completed",
            step_id=1,
            details={"output": huge_str},
        )
        logs = self.logger.get_task_logs("t2")
        logged_output = logs[0]["details"]["output"]
        self.assertTrue(len(logged_output) < 11_000)
        self.assertTrue(logged_output.endswith("[TRUNCATED]"))

    def test_invalid_task_id_rejected(self):
        with self.assertRaises(ValueError):
            self.logger.log_event(task_id="", event="test_event")
        with self.assertRaises(ValueError):
            self.logger.log_event(task_id="   ", event="test_event")
        with self.assertRaises(TypeError):
            self.logger.log_event(task_id=123, event="test_event")

    def test_invalid_event_rejected(self):
        with self.assertRaises(ValueError):
            self.logger.log_event(task_id="t1", event="")
        with self.assertRaises(ValueError):
            self.logger.log_event(task_id="t1", event="   ")
        with self.assertRaises(TypeError):
            self.logger.log_event(task_id="t1", event=123)

    def test_invalid_step_id_rejected(self):
        with self.assertRaises(TypeError):
            self.logger.log_event(task_id="t1", event="test_event", step_id="1")
        with self.assertRaises(TypeError):
            self.logger.log_event(task_id="t1", event="test_event", step_id=True)


if __name__ == "__main__":
    unittest.main()
