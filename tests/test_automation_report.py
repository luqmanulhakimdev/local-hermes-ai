import unittest

from src.automation.evaluation import (
    EvaluationSummary,
    generate_evaluation_report,
)


class TestEvaluationReport(unittest.TestCase):
    def test_full_report_generation(self):
        summary = EvaluationSummary(
            total_cases=5,
            planning_accuracy=1.0,
            tool_selection_accuracy=1.0,
            execution_outcome_accuracy=1.0,
        )
        report = generate_evaluation_report(
            summary=summary,
            recovery_success=1.0,
            trace_completeness=1.0,
            approval_compliance=1.0,
            failures=None,
        )

        self.assertIn("Stage 13 Evaluation Report", report)
        self.assertIn("Total cases: 5", report)
        self.assertIn("Planning accuracy: 1.00", report)
        self.assertIn("Tool selection accuracy: 1.00", report)
        self.assertIn("Execution outcome accuracy: 1.00", report)
        self.assertIn("Recovery success: 1.00", report)
        self.assertIn("Trace completeness: 1.00", report)
        self.assertIn("Approval compliance: 1.00", report)
        self.assertIn("Failures\n--------\nNone", report)

    def test_report_with_na_and_boolean_metrics(self):
        summary = EvaluationSummary(
            total_cases=3,
            planning_accuracy=0.67,
            tool_selection_accuracy=0.67,
            execution_outcome_accuracy=0.33,
        )
        report = generate_evaluation_report(
            summary=summary,
            recovery_success=None,
            trace_completeness=True,
            approval_compliance=None,
            failures=["calculator_power: execution failed", "read_project_file: wrong tool"],
        )

        self.assertIn("Total cases: 3", report)
        self.assertIn("Planning accuracy: 0.67", report)
        self.assertIn("Recovery success: N/A", report)
        self.assertIn("Trace completeness: True", report)
        self.assertIn("Approval compliance: N/A", report)
        self.assertIn("- calculator_power: execution failed", report)
        self.assertIn("- read_project_file: wrong tool", report)

    def test_invalid_summary_type_rejected(self):
        with self.assertRaises(TypeError):
            generate_evaluation_report("not_a_summary")


if __name__ == "__main__":
    unittest.main()
