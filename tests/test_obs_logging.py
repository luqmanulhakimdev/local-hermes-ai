import unittest
from unittest.mock import MagicMock

from src.observability.logging_schema import (
    ObservabilityLogger,
    StructuredLogRecord,
)


class TestObservabilityLogging(unittest.TestCase):
    def test_structured_record_fields_and_secret_redaction(self):
        rec = StructuredLogRecord(
            timestamp="2026-11-26T10:00:00+00:00",
            level="INFO",
            event="llm_completed",
            run_id="run-1",
            task_id="task-1",
            step_id=1,
            component="planner",
            status="completed",
            duration_ms=125.5,
            metadata={"api_key": "sk-secret-123", "model": "qwen3"},
        )
        self.assertEqual(rec.metadata["api_key"], "[REDACTED]")
        self.assertEqual(rec.metadata["model"], "qwen3")

    def test_invalid_level_or_event_rejected(self):
        with self.assertRaises(ValueError):
            StructuredLogRecord(
                timestamp="2026-11-26T10:00:00+00:00",
                level="INVALID",
                event="run_started",
                run_id="run-1",
            )
        with self.assertRaises(ValueError):
            StructuredLogRecord(
                timestamp="2026-11-26T10:00:00+00:00",
                level="INFO",
                event="unregistered_event",
                run_id="run-1",
            )

    def test_logger_correlation_retention_and_best_effort(self):
        broken_task_logger = MagicMock()
        broken_task_logger.log_event.side_effect = RuntimeError("DB locked")

        logger = ObservabilityLogger(task_logger=broken_task_logger, max_events=2)
        # Must not raise even though task_logger fails
        logger.emit("run_started", run_id="r1", task_id="t1")
        logger.emit("step_started", run_id="r1", task_id="t1", step_id=1)
        logger.emit("run_completed", run_id="r2", task_id="t2")

        all_recs = logger.get_records()
        self.assertEqual(len(all_recs), 2)  # max_events=2 retention enforced
        self.assertEqual(len(logger.get_records(run_id="r1")), 1)
        self.assertEqual(len(logger.get_records(run_id="r2")), 1)


if __name__ == "__main__":
    unittest.main()
