import unittest

from src.automation.evaluation import (
    EvaluationSummary,
    calculate_evaluation_summary,
)
from src.automation.evaluation_dataset import EvaluationCase
from src.automation.models import TaskPlan, TaskStatus, TaskStep


class TestAggregateEvaluation(unittest.TestCase):
    def setUp(self):
        self.case1 = EvaluationCase(
            case_id="case_1",
            request="Hitung 1 + 1",
            expected_tools=["calculator"],
            expected_step_count=1,
            expected_success=True,
            description="Case 1",
        )
        self.case2 = EvaluationCase(
            case_id="case_2",
            request="Waktu sekarang",
            expected_tools=["current_time"],
            expected_step_count=1,
            expected_success=True,
            description="Case 2",
        )

    def test_perfect_accuracy(self):
        cases = [self.case1, self.case2]
        plans = {
            "case_1": TaskPlan(
                description="Hitung 1 + 1",
                steps=[TaskStep(step_id=1, tool="calculator")],
                status=TaskStatus.COMPLETED,
            ),
            "case_2": TaskPlan(
                description="Waktu sekarang",
                steps=[TaskStep(step_id=1, tool="current_time")],
                status=TaskStatus.COMPLETED,
            ),
        }

        summary = calculate_evaluation_summary(cases, plans)

        self.assertEqual(summary.total_cases, 2)
        self.assertEqual(summary.planning_accuracy, 1.0)
        self.assertEqual(summary.tool_selection_accuracy, 1.0)
        self.assertEqual(summary.execution_outcome_accuracy, 1.0)

    def test_partial_accuracy(self):
        cases = [self.case1, self.case2]
        # case 1 has wrong tool selection (current_time instead of calculator)
        # case 2 is correct but failed execution
        plans = {
            "case_1": TaskPlan(
                description="Hitung 1 + 1",
                steps=[TaskStep(step_id=1, tool="current_time")],
                status=TaskStatus.COMPLETED,
            ),
            "case_2": TaskPlan(
                description="Waktu sekarang",
                steps=[TaskStep(step_id=1, tool="current_time")],
                status=TaskStatus.COMPLETED,
            ),
        }
        executed = {
            "case_1": TaskPlan(
                description="Hitung 1 + 1",
                steps=[TaskStep(step_id=1, tool="current_time")],
                status=TaskStatus.COMPLETED,
            ),
            "case_2": TaskPlan(
                description="Waktu sekarang",
                steps=[TaskStep(step_id=1, tool="current_time")],
                status=TaskStatus.FAILED,  # mismatch with expected_success=True
            ),
        }

        summary = calculate_evaluation_summary(cases, plans, executed)

        self.assertEqual(summary.total_cases, 2)
        # planning: case_1 failed tool sequence -> 1/2 = 0.5
        self.assertEqual(summary.planning_accuracy, 0.5)
        # tool selection: case_1 failed -> 1/2 = 0.5
        self.assertEqual(summary.tool_selection_accuracy, 0.5)
        # execution outcome: case_1 matched (COMPLETED == True), case_2 mismatched (FAILED != True) -> 1/2 = 0.5
        self.assertEqual(summary.execution_outcome_accuracy, 0.5)

    def test_zero_accuracy(self):
        cases = [self.case1]
        plans = {
            "case_1": TaskPlan(
                description="Hitung 1 + 1",
                steps=[
                    TaskStep(step_id=1, tool="wrong_tool"),
                    TaskStep(step_id=2, tool="wrong_tool"),
                ],
                status=TaskStatus.FAILED,
            ),
        }

        summary = calculate_evaluation_summary(cases, plans)

        self.assertEqual(summary.total_cases, 1)
        self.assertEqual(summary.planning_accuracy, 0.0)
        self.assertEqual(summary.tool_selection_accuracy, 0.0)
        self.assertEqual(summary.execution_outcome_accuracy, 0.0)

    def test_empty_dataset_rejected(self):
        with self.assertRaises(ValueError):
            calculate_evaluation_summary([], {})

    def test_missing_plan_rejected(self):
        cases = [self.case1, self.case2]
        plans = {
            "case_1": TaskPlan(
                description="Hitung 1 + 1",
                steps=[TaskStep(step_id=1, tool="calculator")],
            )
        }

        with self.assertRaises(ValueError):
            calculate_evaluation_summary(cases, plans)

    def test_missing_executed_task_rejected(self):
        cases = [self.case1, self.case2]
        plans = {
            "case_1": TaskPlan(
                description="Hitung 1 + 1",
                steps=[TaskStep(step_id=1, tool="calculator")],
            ),
            "case_2": TaskPlan(
                description="Waktu sekarang",
                steps=[TaskStep(step_id=1, tool="current_time")],
            ),
        }
        executed = {
            "case_1": TaskPlan(
                description="Hitung 1 + 1",
                steps=[TaskStep(step_id=1, tool="calculator")],
            )
        }

        with self.assertRaises(ValueError):
            calculate_evaluation_summary(cases, plans, executed)

    def test_dataclass_validation(self):
        with self.assertRaises(ValueError):
            EvaluationSummary(
                total_cases=0,  # <= 0
                planning_accuracy=1.0,
                tool_selection_accuracy=1.0,
                execution_outcome_accuracy=1.0,
            )

        with self.assertRaises(ValueError):
            EvaluationSummary(
                total_cases=1,
                planning_accuracy=1.5,  # > 1.0
                tool_selection_accuracy=1.0,
                execution_outcome_accuracy=1.0,
            )

        with self.assertRaises(ValueError):
            EvaluationSummary(
                total_cases=1,
                planning_accuracy=-0.1,  # < 0.0
                tool_selection_accuracy=1.0,
                execution_outcome_accuracy=1.0,
            )


if __name__ == "__main__":
    unittest.main()
