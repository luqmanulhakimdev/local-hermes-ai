import unittest

from src.automation.tracing import StepTrace, TaskTrace, build_task_trace


class TestAutomationTracing(unittest.TestCase):
    def test_reconstruct_successful_multi_step_trace(self):
        logs = [
            {
                "task_id": "task_123",
                "step_id": None,
                "event": "task_started",
                "details": {"description": "Calculate 1 + 1 and 2 * 2"},
                "created_at": "2026-11-23T10:00:00Z",
            },
            {
                "task_id": "task_123",
                "step_id": 1,
                "event": "step_started",
                "details": {"tool": "calculator", "arguments": {"expr": "1+1"}},
                "created_at": "2026-11-23T10:00:01Z",
            },
            {
                "task_id": "task_123",
                "step_id": 1,
                "event": "step_completed",
                "details": {"tool": "calculator", "output": 2},
                "created_at": "2026-11-23T10:00:02Z",
            },
            {
                "task_id": "task_123",
                "step_id": 2,
                "event": "step_started",
                "details": {"tool": "calculator", "arguments": {"expr": "2*2"}},
                "created_at": "2026-11-23T10:00:03Z",
            },
            {
                "task_id": "task_123",
                "step_id": 2,
                "event": "step_completed",
                "details": {"tool": "calculator", "output": 4},
                "created_at": "2026-11-23T10:00:04Z",
            },
            {
                "task_id": "task_123",
                "step_id": None,
                "event": "task_completed",
                "details": {"steps_completed": 2},
                "created_at": "2026-11-23T10:00:05Z",
            },
        ]

        trace = build_task_trace(logs)

        self.assertEqual(trace.task_id, "task_123")
        self.assertTrue(trace.started)
        self.assertTrue(trace.completed)
        self.assertFalse(trace.failed)
        self.assertEqual(trace.description, "Calculate 1 + 1 and 2 * 2")
        self.assertEqual(len(trace.steps), 2)

        step1 = trace.steps[1]
        self.assertEqual(step1.step_id, 1)
        self.assertEqual(step1.tool, "calculator")
        self.assertEqual(step1.arguments, {"expr": "1+1"})
        self.assertTrue(step1.started)
        self.assertTrue(step1.completed)
        self.assertFalse(step1.failed)
        self.assertEqual(step1.output, 2)

        step2 = trace.steps[2]
        self.assertEqual(step2.step_id, 2)
        self.assertEqual(step2.tool, "calculator")
        self.assertEqual(step2.output, 4)

    def test_reconstruct_failed_task_trace(self):
        logs = [
            {
                "task_id": "task_fail",
                "step_id": None,
                "event": "task_started",
                "details": {"description": "Failing task"},
                "created_at": "2026-11-23T10:00:00Z",
            },
            {
                "task_id": "task_fail",
                "step_id": 1,
                "event": "step_started",
                "details": {"tool": "bad_tool", "arguments": {}},
                "created_at": "2026-11-23T10:00:01Z",
            },
            {
                "task_id": "task_fail",
                "step_id": 1,
                "event": "step_failed",
                "details": {"tool": "bad_tool", "error": "ValueError: Crash"},
                "created_at": "2026-11-23T10:00:02Z",
            },
            {
                "task_id": "task_fail",
                "step_id": 1,
                "event": "task_failed",
                "details": {"error": "ValueError: Crash"},
                "created_at": "2026-11-23T10:00:03Z",
            },
        ]

        trace = build_task_trace(logs)

        self.assertTrue(trace.started)
        self.assertFalse(trace.completed)
        self.assertTrue(trace.failed)
        self.assertEqual(trace.error, "ValueError: Crash")

        step1 = trace.steps[1]
        self.assertTrue(step1.started)
        self.assertFalse(step1.completed)
        self.assertTrue(step1.failed)
        self.assertEqual(step1.error, "ValueError: Crash")

    def test_reconstruct_approval_flow_trace(self):
        logs = [
            {
                "task_id": "task_appr",
                "step_id": None,
                "event": "task_started",
                "details": {},
                "created_at": "2026-11-23T10:00:00Z",
            },
            {
                "task_id": "task_appr",
                "step_id": 1,
                "event": "step_started",
                "details": {"tool": "send_email", "arguments": {"to": "admin"}},
                "created_at": "2026-11-23T10:00:01Z",
            },
            {
                "task_id": "task_appr",
                "step_id": 1,
                "event": "approval_requested",
                "details": {"tool": "send_email", "arguments": {"to": "admin"}},
                "created_at": "2026-11-23T10:00:02Z",
            },
            {
                "task_id": "task_appr",
                "step_id": 1,
                "event": "approval_granted",
                "details": {"tool": "send_email"},
                "created_at": "2026-11-23T10:00:03Z",
            },
            {
                "task_id": "task_appr",
                "step_id": 1,
                "event": "step_completed",
                "details": {"tool": "send_email", "output": "sent"},
                "created_at": "2026-11-23T10:00:04Z",
            },
            {
                "task_id": "task_appr",
                "step_id": None,
                "event": "task_completed",
                "details": {},
                "created_at": "2026-11-23T10:00:05Z",
            },
        ]

        trace = build_task_trace(logs)
        step1 = trace.steps[1]
        self.assertTrue(step1.approval_requested)
        self.assertTrue(step1.approval_granted)
        self.assertFalse(step1.approval_denied)
        self.assertTrue(step1.completed)

    def test_reconstruct_approval_denied_trace(self):
        logs = [
            {
                "task_id": "task_denied",
                "step_id": None,
                "event": "task_started",
                "details": {},
                "created_at": "2026-11-23T10:00:00Z",
            },
            {
                "task_id": "task_denied",
                "step_id": 1,
                "event": "step_started",
                "details": {"tool": "delete_all"},
                "created_at": "2026-11-23T10:00:01Z",
            },
            {
                "task_id": "task_denied",
                "step_id": 1,
                "event": "approval_requested",
                "details": {"tool": "delete_all"},
                "created_at": "2026-11-23T10:00:02Z",
            },
            {
                "task_id": "task_denied",
                "step_id": 1,
                "event": "approval_denied",
                "details": {"tool": "delete_all"},
                "created_at": "2026-11-23T10:00:03Z",
            },
            {
                "task_id": "task_denied",
                "step_id": 1,
                "event": "step_failed",
                "details": {"tool": "delete_all", "error": "PermissionError: Denied"},
                "created_at": "2026-11-23T10:00:04Z",
            },
            {
                "task_id": "task_denied",
                "step_id": None,
                "event": "task_failed",
                "details": {},
                "created_at": "2026-11-23T10:00:05Z",
            },
        ]

        trace = build_task_trace(logs)
        step1 = trace.steps[1]
        self.assertTrue(step1.approval_requested)
        self.assertFalse(step1.approval_granted)
        self.assertTrue(step1.approval_denied)
        self.assertTrue(step1.failed)

    def test_reconstruct_resumed_task_trace(self):
        logs = [
            {
                "task_id": "task_resume",
                "step_id": None,
                "event": "task_started",
                "details": {},
                "created_at": "2026-11-23T10:00:00Z",
            },
            {
                "task_id": "task_resume",
                "step_id": 1,
                "event": "step_started",
                "details": {"tool": "t1"},
                "created_at": "2026-11-23T10:00:01Z",
            },
            {
                "task_id": "task_resume",
                "step_id": 1,
                "event": "step_completed",
                "details": {"tool": "t1", "output": "ok"},
                "created_at": "2026-11-23T10:00:02Z",
            },
            {
                "task_id": "task_resume",
                "step_id": None,
                "event": "task_resumed",
                "details": {},
                "created_at": "2026-11-23T10:05:00Z",
            },
            {
                "task_id": "task_resume",
                "step_id": 2,
                "event": "step_started",
                "details": {"tool": "t2"},
                "created_at": "2026-11-23T10:05:01Z",
            },
            {
                "task_id": "task_resume",
                "step_id": 2,
                "event": "step_completed",
                "details": {"tool": "t2", "output": "ok2"},
                "created_at": "2026-11-23T10:05:02Z",
            },
            {
                "task_id": "task_resume",
                "step_id": None,
                "event": "task_completed",
                "details": {},
                "created_at": "2026-11-23T10:05:03Z",
            },
        ]

        trace = build_task_trace(logs)
        self.assertTrue(trace.started)
        self.assertTrue(trace.resumed)
        self.assertTrue(trace.completed)
        self.assertEqual(len(trace.steps), 2)

    def test_invalid_logs_rejected(self):
        with self.assertRaises(TypeError):
            build_task_trace("not_a_list")

        with self.assertRaises(ValueError):
            build_task_trace([])

        with self.assertRaises(ValueError):
            build_task_trace([{"event": "task_started"}])  # missing task_id

        with self.assertRaises(TypeError):
            build_task_trace(["not_a_dict"])

        with self.assertRaises(ValueError):
            build_task_trace([
                {"task_id": "t1", "event": "task_started"},
                {"task_id": "t2", "event": "task_completed"},
            ])


if __name__ == "__main__":
    unittest.main()
