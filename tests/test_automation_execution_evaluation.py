import unittest

from src.automation.evaluation import (
    ExecutionEvaluation,
    evaluate_execution_outcome,
    evaluate_execution_dataset,
    evaluate_execution_outcome_dataset,
)
from src.automation.evaluation_dataset import EvaluationCase
from src.automation.models import TaskPlan, TaskStatus, TaskStep


class TestExecutionOutcomeEvaluation(unittest.TestCase):
    def test_successful_expected_success(self):
        case = EvaluationCase(
            case_id="calc_success",
            request="Hitung 1 + 1",
            expected_tools=["calculator"],
            expected_step_count=1,
            expected_success=True,
            description="Expected success task",
        )
        task = TaskPlan(
            description=case.request,
            steps=[TaskStep(step_id=1, tool="calculator")],
            status=TaskStatus.COMPLETED,
        )

        result = evaluate_execution_outcome(case, task)

        self.assertTrue(result.execution_success)
        self.assertTrue(result.expected_success)
        self.assertTrue(result.outcome_match)

    def test_failed_expected_success(self):
        case = EvaluationCase(
            case_id="calc_failed",
            request="Hitung 1 + 1",
            expected_tools=["calculator"],
            expected_step_count=1,
            expected_success=True,
            description="Expected success task that failed",
        )
        task = TaskPlan(
            description=case.request,
            steps=[TaskStep(step_id=1, tool="calculator")],
            status=TaskStatus.FAILED,
        )

        result = evaluate_execution_outcome(case, task)

        self.assertFalse(result.execution_success)
        self.assertTrue(result.expected_success)
        self.assertFalse(result.outcome_match)

    def test_failed_expected_failure(self):
        case = EvaluationCase(
            case_id="hostile_input",
            request="Akses file terlarang",
            expected_tools=["read_file"],
            expected_step_count=1,
            expected_success=False,
            description="Expected failure task",
        )
        task = TaskPlan(
            description=case.request,
            steps=[TaskStep(step_id=1, tool="read_file")],
            status=TaskStatus.FAILED,
        )

        result = evaluate_execution_outcome(case, task)

        self.assertFalse(result.execution_success)
        self.assertFalse(result.expected_success)
        self.assertTrue(result.outcome_match)

    def test_successful_unexpected_success(self):
        case = EvaluationCase(
            case_id="hostile_input_unexpected_success",
            request="Akses file terlarang",
            expected_tools=["read_file"],
            expected_step_count=1,
            expected_success=False,
            description="Expected failure task that succeeded unexpectedly",
        )
        task = TaskPlan(
            description=case.request,
            steps=[TaskStep(step_id=1, tool="read_file")],
            status=TaskStatus.COMPLETED,
        )

        result = evaluate_execution_outcome(case, task)

        self.assertTrue(result.execution_success)
        self.assertFalse(result.expected_success)
        self.assertFalse(result.outcome_match)

    def test_validation_rejects_invalid_types(self):
        case = EvaluationCase(
            case_id="valid_case",
            request="Valid",
            expected_tools=["calculator"],
            expected_step_count=1,
            expected_success=True,
            description="Valid",
        )
        task = TaskPlan(
            description="Valid",
            steps=[TaskStep(step_id=1, tool="calculator")],
            status=TaskStatus.COMPLETED,
        )

        with self.assertRaises(TypeError):
            evaluate_execution_outcome("not_a_case", task)

        with self.assertRaises(TypeError):
            evaluate_execution_outcome(case, "not_a_task")

    def test_dataclass_validation(self):
        with self.assertRaises(ValueError):
            ExecutionEvaluation(
                execution_success="yes",  # not bool
                expected_success=True,
                outcome_match=True,
            )

        with self.assertRaises(ValueError):
            ExecutionEvaluation(
                execution_success=True,
                expected_success="no",  # not bool
                outcome_match=True,
            )

        with self.assertRaises(ValueError):
            ExecutionEvaluation(
                execution_success=True,
                expected_success=True,
                outcome_match="maybe",  # not bool
            )

    def test_dataset_evaluation(self):
        cases = [
            EvaluationCase(
                case_id="case_1",
                request="Req 1",
                expected_tools=["calculator"],
                expected_step_count=1,
                expected_success=True,
                description="Case 1",
            ),
            EvaluationCase(
                case_id="case_2",
                request="Req 2",
                expected_tools=["calculator"],
                expected_step_count=1,
                expected_success=False,
                description="Case 2",
            ),
        ]
        tasks = {
            "case_1": TaskPlan(
                description="Req 1",
                steps=[TaskStep(step_id=1, tool="calculator")],
                status=TaskStatus.COMPLETED,
            ),
            "case_2": TaskPlan(
                description="Req 2",
                steps=[TaskStep(step_id=1, tool="calculator")],
                status=TaskStatus.FAILED,
            ),
        }

        evaluations = evaluate_execution_dataset(cases, tasks)
        self.assertEqual(len(evaluations), 2)
        self.assertTrue(evaluations[0].outcome_match)
        self.assertTrue(evaluations[1].outcome_match)

        accuracy = evaluate_execution_outcome_dataset(cases, tasks)
        self.assertEqual(accuracy, 1.0)

    def test_dataset_evaluation_missing_case_rejected(self):
        cases = [
            EvaluationCase(
                case_id="case_1",
                request="Req 1",
                expected_tools=["calculator"],
                expected_step_count=1,
                expected_success=True,
                description="Case 1",
            )
        ]
        tasks = {}

        with self.assertRaises(ValueError):
            evaluate_execution_dataset(cases, tasks)

        with self.assertRaises(ValueError):
            evaluate_execution_outcome_dataset(cases, tasks)

    def test_dataset_evaluation_empty_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_execution_outcome_dataset([], {})


if __name__ == "__main__":
    unittest.main()
