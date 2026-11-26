import unittest

from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.observability.inspector import RunInspector, format_observability_summary


class TestRunInspector(unittest.TestCase):
    def setUp(self):
        self.inspector = RunInspector()
        self.logs = [
            {"event": "run_started", "run_id": "run-abc", "task_id": "task-1", "timestamp": "2026-11-26T10:00:00+00:00"},
            {"event": "llm_completed", "run_id": "run-abc", "task_id": "task-1", "details": {"model": "qwen3:4b", "input_tokens": 100, "output_tokens": 50}, "timestamp": "2026-11-26T10:00:00.400000+00:00"},
            {"event": "step_started", "run_id": "run-abc", "task_id": "task-1", "step_id": 1, "details": {"tool": "calculator"}, "timestamp": "2026-11-26T10:00:00.500000+00:00"},
            {"event": "step_completed", "run_id": "run-abc", "task_id": "task-1", "step_id": 1, "details": {"tool": "calculator", "output": "X" * 500}, "timestamp": "2026-11-26T10:00:00.700000+00:00"},
            {"event": "run_completed", "run_id": "run-abc", "task_id": "task-1", "timestamp": "2026-11-26T10:00:01+00:00"},
        ]
        self.task = TaskPlan(
            task_id="task-1",
            description="Test task",
            steps=[TaskStep(1, "calculator", {"expression": "1+1"}, StepStatus.COMPLETED, "X" * 500)],
            status=TaskStatus.COMPLETED,
        )

    def test_inspect_run_and_truncate_output(self):
        report = self.inspector.inspect_run("run-abc", self.logs, task=self.task)
        self.assertIsNotNone(report)
        self.assertEqual(report.status, "completed")
        self.assertEqual(report.model, "qwen3:4b")
        self.assertEqual(report.token_usage.total_tokens, 150)
        self.assertIsNone(report.estimated_cost)
        self.assertTrue(report.steps[0].output_summary.endswith("... [TRUNCATED]"))

        summary = format_observability_summary(report)
        self.assertIn("OBSERVABILITY SUMMARY", summary)
        self.assertIn("ID: run-abc", summary)
        self.assertIn("Estimated cost: UNKNOWN", summary)
        self.assertIn("Total tokens: 150", summary)

    def test_missing_run_returns_none(self):
        self.assertIsNone(self.inspector.inspect_run("nonexistent", self.logs))

    def test_search_runs_filtering(self):
        logs = self.logs + [
            {"event": "run_started", "run_id": "run-fail", "task_id": "task-2", "timestamp": "2026-11-26T11:00:00+00:00"},
            {"event": "run_failed", "run_id": "run-fail", "task_id": "task-2", "details": {"error": "TimeoutError"}, "timestamp": "2026-11-26T11:00:02+00:00"},
        ]
        self.assertEqual(self.inspector.search_runs(logs, status="completed"), ["run-abc"])
        self.assertEqual(self.inspector.search_runs(logs, status="failed"), ["run-fail"])
        self.assertEqual(self.inspector.search_runs(logs, error_category="timeout_error"), ["run-fail"])


if __name__ == "__main__":
    unittest.main()
