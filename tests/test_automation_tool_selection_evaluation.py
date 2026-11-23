import unittest

from src.automation.evaluation import evaluate_tool_selection
from src.automation.evaluation_dataset import EvaluationCase
from src.automation.models import TaskPlan, TaskStep

from src.automation.evaluation import (
    evaluate_tool_selection,
    evaluate_tool_selection_dataset,
)


class TestToolSelectionEvaluation(unittest.TestCase):
    def test_correct_tool_selection(self):
        case = EvaluationCase(
            case_id="calculator_basic",
            request="Hitung 10 + 20",
            expected_tools=["calculator"],
            expected_step_count=1,
            expected_success=True,
            description="Basic calculator task",
        )

        plan = TaskPlan(
            description=case.request,
            steps=[
                TaskStep(
                    step_id=1,
                    tool="calculator",
                    arguments={"expression": "10 + 20"},
                )
            ],
        )

        result = evaluate_tool_selection(case, plan)

        self.assertTrue(result)

    def test_wrong_tool_selection(self):
        case = EvaluationCase(
            case_id="calculator_basic",
            request="Hitung 10 + 20",
            expected_tools=["calculator"],
            expected_step_count=1,
            expected_success=True,
            description="Basic calculator task",
        )

        plan = TaskPlan(
            description=case.request,
            steps=[
                TaskStep(
                    step_id=1,
                    tool="current_time",
                    arguments={},
                )
            ],
        )

        result = evaluate_tool_selection(case, plan)

        self.assertFalse(result)

    def test_wrong_tool_order(self):
        case = EvaluationCase(
            case_id="multi_step",
            request="Lakukan dua langkah",
            expected_tools=["calculator", "current_time"],
            expected_step_count=2,
            expected_success=True,
            description="Multi-step tool selection",
        )

        plan = TaskPlan(
            description=case.request,
            steps=[
                TaskStep(
                    step_id=1,
                    tool="current_time",
                    arguments={},
                ),
                TaskStep(
                    step_id=2,
                    tool="calculator",
                    arguments={},
                ),
            ],
        )

        result = evaluate_tool_selection(case, plan)

        self.assertFalse(result)

    def test_tool_selection_dataset_accuracy(self):
        cases = [
            EvaluationCase(
                case_id="calculator_basic",
                request="Hitung 10 + 20",
                expected_tools=["calculator"],
                expected_step_count=1,
                expected_success=True,
                description="Basic calculator task",
            ),
            EvaluationCase(
                case_id="current_time",
                request="Tampilkan waktu saat ini",
                expected_tools=["current_time"],
                expected_step_count=1,
                expected_success=True,
                description="Current time task",
            ),
        ]

        plans = {
            "calculator_basic": TaskPlan(
                description=cases[0].request,
                steps=[
                    TaskStep(
                        step_id=1,
                        tool="calculator",
                        arguments={},
                    )
                ],
            ),
            "current_time": TaskPlan(
                description=cases[1].request,
                steps=[
                    TaskStep(
                        step_id=1,
                        tool="current_time",
                        arguments={},
                    )
                ],
            ),
        }

        accuracy = evaluate_tool_selection_dataset(
            cases,
            plans,
        )

        self.assertEqual(accuracy, 1.0)


if __name__ == "__main__":
    unittest.main()