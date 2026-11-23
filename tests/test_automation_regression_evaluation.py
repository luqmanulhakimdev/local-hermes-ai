import unittest

from src.automation.evaluation import (
    RegressionEvaluator,
    run_regression_evaluation,
)
from src.automation.evaluation_cases import EVALUATION_CASES, REFERENCE_PLANS
from src.automation.models import TaskPlan, TaskStep, TaskStatus, StepStatus


class TestRegressionEvaluator(unittest.TestCase):
    def test_regression_with_default_golden_dataset(self):
        evaluator = RegressionEvaluator()
        summary = evaluator.evaluate()

        self.assertEqual(summary.total_cases, len(EVALUATION_CASES))
        self.assertEqual(summary.planning_accuracy, 1.0)
        self.assertEqual(summary.tool_selection_accuracy, 1.0)
        self.assertEqual(summary.execution_outcome_accuracy, 1.0)

    def test_summary_text_output(self):
        evaluator = RegressionEvaluator()
        summary = evaluator.evaluate()
        text = evaluator.summary_text(summary)

        self.assertIn("Evaluation Summary", text)
        self.assertIn(f"Total cases: {len(EVALUATION_CASES)}", text)
        self.assertIn("Planning accuracy: 1.00", text)
        self.assertIn("Tool selection accuracy: 1.00", text)
        self.assertIn("Execution outcome accuracy: 1.00", text)

    def test_run_regression_evaluation_helper(self):
        summary, text = run_regression_evaluation()
        self.assertEqual(summary.total_cases, len(EVALUATION_CASES))
        self.assertEqual(summary.planning_accuracy, 1.0)
        self.assertIn("Planning accuracy: 1.00", text)

    def test_strict_mode_passes_on_perfect_scores(self):
        evaluator = RegressionEvaluator()
        summary = evaluator.evaluate(strict=True)
        self.assertEqual(summary.planning_accuracy, 1.0)

    def test_strict_mode_fails_on_imperfect_scores(self):
        flawed_plans = dict(REFERENCE_PLANS)
        flawed_plans["calculator_basic"] = TaskPlan(
            task_id="flawed",
            description="Flawed plan",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="wrong_tool",
                    arguments={},
                    status=StepStatus.COMPLETED,
                )
            ],
            status=TaskStatus.COMPLETED,
        )
        evaluator = RegressionEvaluator(reference_plans=flawed_plans)
        with self.assertRaises(RuntimeError):
            evaluator.evaluate(strict=True)

    def test_missing_case_plan_raises_error(self):
        incomplete_plans = {
            "calculator_basic": REFERENCE_PLANS["calculator_basic"]
        }
        evaluator = RegressionEvaluator(reference_plans=incomplete_plans)
        with self.assertRaises(ValueError):
            evaluator.evaluate()


if __name__ == "__main__":
    unittest.main()
