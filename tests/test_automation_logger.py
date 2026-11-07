import tempfile
import unittest
from pathlib import Path

from src.automation.logger import TaskLogger


class TestTaskLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.logger = TaskLogger(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_log_event(self):
        self.logger.log_event(
            task_id="task-1",
            event="task_started",
            details={"description": "Test task"},
        )

        logs = self.logger.get_task_logs("task-1")

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["event"], "task_started")
        self.assertEqual(
            logs[0]["details"]["description"],
            "Test task",
        )

    def test_log_step_event(self):
        self.logger.log_event(
            task_id="task-1",
            step_id=1,
            event="step_completed",
            details={"tool": "read_file"},
        )

        logs = self.logger.get_task_logs("task-1")

        self.assertEqual(logs[0]["step_id"], 1)
        self.assertEqual(logs[0]["event"], "step_completed")

    def test_logs_are_separated_by_task(self):
        self.logger.log_event("task-1", "started")
        self.logger.log_event("task-2", "started")

        logs = self.logger.get_task_logs("task-1")

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["task_id"], "task-1")

    def test_empty_task_id_rejected(self):
        with self.assertRaises(ValueError):
            self.logger.log_event("", "started")

    def test_empty_event_rejected(self):
        with self.assertRaises(ValueError):
            self.logger.log_event("task-1", "")


if __name__ == "__main__":
    unittest.main()