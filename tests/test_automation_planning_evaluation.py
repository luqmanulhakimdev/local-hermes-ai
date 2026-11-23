import unittest

from src.automation.evaluation import evaluate_planning
from src.automation.evaluation_dataset import EvaluationCase
from src.automation.models import TaskPlan, TaskStep
from src.automation.evaluation_cases import EVALUATION_CASES

from src.automation.evaluation import (
    evaluate_planning,
    evaluate_planning_dataset,
)


class TestPlanningEvaluation(unittest.TestCase):
    def test_correct_plan(self):
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

        result = evaluate_planning(case, plan)

        self.assertTrue(result.tool_sequence_correct)
        self.assertTrue(result.step_count_correct)
        self.assertTrue(result.planning_success)

    def test_wrong_tool(self):
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

        result = evaluate_planning(case, plan)

        self.assertFalse(result.tool_sequence_correct)
        self.assertTrue(result.step_count_correct)
        self.assertFalse(result.planning_success)

    def test_wrong_step_count(self):
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
                ),
                TaskStep(
                    step_id=2,
                    tool="calculator",
                    arguments={"expression": "5 + 5"},
                ),
            ],
        )

        result = evaluate_planning(case, plan)

        self.assertTrue(result.tool_sequence_correct)
        self.assertFalse(result.step_count_correct)
        self.assertFalse(result.planning_success)

    def test_wrong_tool_order(self):
        case = EvaluationCase(
            case_id="multi_step_calculation",
            request="Hitung 10 + 20 lalu kalikan hasilnya dengan 2",
            expected_tools=["calculator", "current_time"],
            expected_step_count=2,
            expected_success=True,
            description="Two-step task with ordered tools",
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
                    arguments={"expression": "10 * 2"},
                ),
            ],
        )

        result = evaluate_planning(case, plan)

        self.assertFalse(result.tool_sequence_correct)
        self.assertTrue(result.step_count_correct)
        self.assertFalse(result.planning_success)

    def test_evaluate_planning_dataset(self):
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
                description="Hitung 10 + 20",
                steps=[
                    TaskStep(
                        step_id=1,
                        tool="calculator",
                        arguments={"expression": "10 + 20"},
                    )
                ],
            ),
            "current_time": TaskPlan(
                description="Tampilkan waktu saat ini",
                steps=[
                    TaskStep(
                        step_id=1,
                        tool="current_time",
                        arguments={},
                    )
                ],
            ),
        }

        results = evaluate_planning_dataset(cases, plans)

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].planning_success)
        self.assertTrue(results[1].planning_success)

    def test_full_evaluation_dataset(self):
        plans = {}

        for case in EVALUATION_CASES:
            plans[case.case_id] = TaskPlan(
                description=case.request,
                steps=[
                    TaskStep(
                        step_id=index,
                        tool=tool,
                        arguments={},
                    )
                    for index, tool in enumerate(
                        case.expected_tools,
                        start=1,
                    )
                ],
            )

        results = evaluate_planning_dataset(
            EVALUATION_CASES,
            plans,
        )

        self.assertEqual(
            len(results),
            len(EVALUATION_CASES),
        )

        for case, result in zip(EVALUATION_CASES, results):
            with self.subTest(case_id=case.case_id):
                self.assertTrue(result.tool_sequence_correct)
                self.assertTrue(result.step_count_correct)
                self.assertTrue(result.planning_success)


if __name__ == "__main__":
    unittest.main()