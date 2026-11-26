import unittest

from src.observability.metrics import (
    PricingConfig,
    calculate_cost,
    compute_error_metrics,
    compute_latency_breakdown,
    compute_token_usage,
)
from src.observability.tracing import build_run_trace


class TestObservabilityMetrics(unittest.TestCase):
    def test_latency_breakdown_measured_and_missing(self):
        logs = [
            {"event": "run_started", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:00+00:00"},
            {"event": "llm_started", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:00+00:00"},
            {"event": "llm_completed", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:00.500000+00:00"},
            {"event": "tool_called", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:00.500000+00:00"},
            {"event": "tool_completed", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:00.800000+00:00"},
            {"event": "run_completed", "run_id": "r1", "task_id": "t1", "timestamp": "2026-11-26T10:00:01+00:00"},
        ]
        trace = build_run_trace("r1", logs)
        lat = compute_latency_breakdown(trace)
        self.assertEqual(lat.total_ms, 1000.0)
        self.assertEqual(lat.llm_ms, 500.0)
        self.assertEqual(lat.tools_ms, 300.0)
        self.assertEqual(lat.other_ms, 200.0)
        self.assertEqual(lat.attribution_mode, "measured")

    def test_error_metrics_categorization_and_zero_denominator(self):
        # Zero denominator returns None rates
        empty_err = compute_error_metrics([])
        self.assertEqual(empty_err.total_errors, 0)
        self.assertIsNone(empty_err.step_error_rate)
        self.assertIsNone(empty_err.tool_error_rate)

        logs = [
            {"event": "run_started"},
            {"event": "step_started", "step_id": 1},
            {"event": "tool_called", "step_id": 1},
            {"event": "tool_failed", "step_id": 1, "details": {"error": "Tool execution timed out"}},
            {"event": "step_failed", "step_id": 1, "details": {"error": "Tool execution timed out"}},
            {"event": "run_failed"},
        ]
        err = compute_error_metrics(logs)
        self.assertEqual(err.failed_runs, 1)
        self.assertEqual(err.failed_steps, 1)
        self.assertEqual(err.failed_tools, 1)
        self.assertEqual(err.step_error_rate, 1.0)
        self.assertEqual(err.tool_error_rate, 1.0)
        self.assertEqual(err.run_error_rate, 1.0)
        self.assertGreaterEqual(err.timeouts, 1)

    def test_token_usage_and_cost_calculation(self):
        logs = [
            {"event": "llm_completed", "details": {"input_tokens": 500, "output_tokens": 100}},
            {"event": "llm_completed", "details": {"input_tokens": 700, "output_tokens": 200}},
        ]
        usage = compute_token_usage(logs)
        self.assertEqual(usage.llm_calls, 2)
        self.assertEqual(usage.input_tokens, 1200)
        self.assertEqual(usage.output_tokens, 300)
        self.assertEqual(usage.total_tokens, 1500)

        # Missing pricing -> None (UNKNOWN)
        self.assertIsNone(calculate_cost(usage, None))

        # Explicit pricing -> accurate calculation
        pricing = PricingConfig(input_cost_per_1k_tokens=0.001, output_cost_per_1k_tokens=0.002)
        cost = calculate_cost(usage, pricing)
        self.assertEqual(cost, 0.0018)

        with self.assertRaises(ValueError):
            PricingConfig(input_cost_per_1k_tokens=-0.1, output_cost_per_1k_tokens=0.0)

    def test_unavailable_token_usage_returns_none(self):
        logs = [{"event": "llm_completed", "details": {"model": "qwen3"}}]
        usage = compute_token_usage(logs)
        self.assertEqual(usage.llm_calls, 1)
        self.assertIsNone(usage.input_tokens)
        self.assertIsNone(usage.output_tokens)
        self.assertIsNone(usage.total_tokens)


if __name__ == "__main__":
    unittest.main()
