import unittest

from src.hermes.evaluation import HermesRunMetrics, evaluate_hermes_run
from src.hermes.protocol import HermesRequest, HermesRequestStatus, HermesResponse


class TestHermesEvaluation(unittest.TestCase):
    def test_run_metrics_validation(self):
        metrics = HermesRunMetrics(
            request_id="req-1",
            operation="run_automation",
            hermes_request_success=True,
            hermes_adapter_success=True,
            hermes_to_automation_success=True,
            hermes_to_rag_success=None,
            approval_compliance=True,
            trace_complete=True,
            recovery_success=None,
        )
        self.assertEqual(metrics.request_id, "req-1")
        self.assertTrue(metrics.hermes_request_success)

    def test_evaluate_hermes_run_automation_success(self):
        req = HermesRequest(request_id="req-1", operation="run_automation", message="Test")
        res = HermesResponse(
            request_id="req-1",
            status=HermesRequestStatus.COMPLETED,
            message="Done",
            task_id="task-1",
        )
        logs = [
            {"event": "hermes_request_started"},
            {"event": "task_started"},
            {"event": "task_completed"},
            {"event": "hermes_request_completed"},
        ]

        metrics = evaluate_hermes_run(request=req, response=res, logs=logs)
        self.assertTrue(metrics.hermes_request_success)
        self.assertTrue(metrics.hermes_adapter_success)
        self.assertTrue(metrics.hermes_to_automation_success)
        self.assertTrue(metrics.trace_complete)

    def test_evaluate_hermes_run_failure(self):
        req = HermesRequest(request_id="req-2", operation="run_automation", message="Failing task")
        res = HermesResponse(
            request_id="req-2",
            status=HermesRequestStatus.FAILED,
            message="Error",
            error="Execution error",
        )
        metrics = evaluate_hermes_run(request=req, response=res, logs=[])
        self.assertFalse(metrics.hermes_request_success)
        self.assertTrue(metrics.hermes_adapter_success)
        self.assertFalse(metrics.hermes_to_automation_success)


if __name__ == "__main__":
    unittest.main()
