import unittest

from src.evaluation.regression import compare_regression


class TestRegressionEvaluation(unittest.TestCase):
    def test_unchanged_and_improved(self):
        baseline = {"planning_accuracy": 0.90, "tool_selection": 0.85}
        current = {"planning_accuracy": 0.90, "tool_selection": 0.95}
        report = compare_regression(baseline, current, allowed_drop=0.02)
        self.assertEqual(report.overall_status, "PASS")
        self.assertEqual(report.unchanged_count, 1)
        self.assertEqual(report.improved_count, 1)
        self.assertEqual(report.regressed_count, 0)

    def test_regression_threshold_detected(self):
        baseline = {"planning_accuracy": 0.95}
        current = {"planning_accuracy": 0.91}
        report = compare_regression(baseline, current, allowed_drop=0.02)
        self.assertEqual(report.overall_status, "REGRESSION")
        self.assertEqual(report.regressed_count, 1)
        self.assertEqual(report.comparisons[0].status, "regressed")

    def test_missing_evidence_marked_unknown(self):
        baseline = {"recovery_success": None, "planning_accuracy": 1.0}
        current = {"recovery_success": 1.0, "planning_accuracy": 1.0}
        report = compare_regression(baseline, current)
        self.assertEqual(report.overall_status, "WARNING")
        self.assertEqual(report.unknown_count, 1)


if __name__ == "__main__":
    unittest.main()
