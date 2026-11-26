import unittest

from src.observability.tracing import build_run_trace


class TestObservabilityTracing(unittest.TestCase):
    def test_successful_lifecycle_and_durations(self):
        logs = [
            {"event": "run_started", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:00+00:00"},
            {"event": "task_started", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:00.100000+00:00"},
            {"event": "retrieval_started", "run_id": "r1", "task_id": "t1", "component": "rag", "timestamp": "2026-11-26T10:00:00.200000+00:00"},
            {"event": "retrieval_completed", "run_id": "r1", "task_id": "t1", "component": "rag", "timestamp": "2026-11-26T10:00:00.500000+00:00"},
            {"event": "step_started", "run_id": "r1", "task_id": "t1", "step_id": 1, "details": {"tool": "calculator"}, "timestamp": "2026-11-26T10:00:00.600000+00:00"},
            {"event": "step_completed", "run_id": "r1", "task_id": "t1", "step_id": 1, "details": {"tool": "calculator", "output": 42}, "timestamp": "2026-11-26T10:00:00.900000+00:00"},
            {"event": "task_completed", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:00.950000+00:00"},
            {"event": "run_completed", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:01+00:00"},
        ]
        trace = build_run_trace("r1", logs)
        self.assertTrue(trace.lifecycle_valid)
        self.assertEqual(trace.status, "completed")
        self.assertEqual(trace.duration_ms, 1000.0)
        self.assertEqual(len(trace.spans), 2)
        self.assertEqual(trace.spans[0].name, "retrieval")
        self.assertEqual(trace.spans[0].duration_ms, 300.0)
        self.assertEqual(trace.spans[1].name, "step_1")
        self.assertEqual(trace.spans[1].duration_ms, 300.0)

    def test_incomplete_and_impossible_transitions_detected(self):
        logs = [
            {"event": "step_completed", "run_id": "r2", "task_id": "t2", "step_id": 1, "timestamp": "bad-ts"},
            {"event": "approval_granted", "run_id": "r2", "task_id": "t2", "step_id": 2, "timestamp": "2026-11-26T10:00:01+00:00"},
        ]
        trace = build_run_trace("r2", logs)
        self.assertFalse(trace.lifecycle_valid)
        self.assertEqual(len(trace.lifecycle_errors), 2)
        self.assertIsNone(trace.duration_ms)  # only 1 valid timestamp

    def test_approval_and_recovery_lifecycle(self):
        logs = [
            {"event": "run_started", "run_id": "r3", "task_id": "t3", "timestamp": "2026-11-26T10:00:00+00:00"},
            {"event": "task_started", "run_id": "r3", "task_id": "t3", "timestamp": "2026-11-26T10:00:00.100000+00:00"},
            {"event": "task_failed", "run_id": "r3", "task_id": "t3", "timestamp": "2026-11-26T10:00:00.200000+00:00"},
            {"event": "task_resumed", "run_id": "r3", "task_id": "t3", "timestamp": "2026-11-26T10:00:00.300000+00:00"},
            {"event": "approval_requested", "run_id": "r3", "task_id": "t3", "step_id": 1, "timestamp": "2026-11-26T10:00:00.400000+00:00"},
            {"event": "approval_granted", "run_id": "r3", "task_id": "t3", "step_id": 1, "timestamp": "2026-11-26T10:00:01.400000+00:00"},
            {"event": "task_completed", "run_id": "r3", "task_id": "t3", "timestamp": "2026-11-26T10:00:01.500000+00:00"},
            {"event": "run_completed", "run_id": "r3", "task_id": "t3", "timestamp": "2026-11-26T10:00:02+00:00"},
        ]
        trace = build_run_trace("r3", logs)
        self.assertTrue(trace.lifecycle_valid)
        self.assertEqual(trace.status, "completed")
        self.assertEqual(trace.spans[0].name, "approval_step_1")
        self.assertEqual(trace.spans[0].duration_ms, 1000.0)


if __name__ == "__main__":
    unittest.main()
