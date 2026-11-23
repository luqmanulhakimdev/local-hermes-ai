import unittest

from src.automation.evaluation_dataset import EvaluationCase


class TestEvaluationCase(unittest.TestCase):
    def test_create_valid_case(self):
        case = EvaluationCase(
            case_id="calculator_basic",
            request="Hitung 10 + 20",
            expected_tools=["calculator"],
            expected_step_count=1,
            expected_success=True,
            description="Basic calculator task",
        )

        self.assertEqual(case.case_id, "calculator_basic")
        self.assertEqual(case.request, "Hitung 10 + 20")
        self.assertEqual(case.expected_tools, ["calculator"])
        self.assertEqual(case.expected_step_count, 1)
        self.assertTrue(case.expected_success)
        self.assertEqual(
            case.description,
            "Basic calculator task",
        )

    def test_empty_case_id_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationCase(
                case_id="",
                request="Hitung 10 + 20",
                expected_tools=["calculator"],
                expected_step_count=1,
                expected_success=True,
                description="Basic calculator task",
            )

    def test_empty_request_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationCase(
                case_id="calculator_basic",
                request="",
                expected_tools=["calculator"],
                expected_step_count=1,
                expected_success=True,
                description="Basic calculator task",
            )

    def test_invalid_step_count_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationCase(
                case_id="calculator_basic",
                request="Hitung 10 + 20",
                expected_tools=["calculator"],
                expected_step_count=0,
                expected_success=True,
                description="Basic calculator task",
            )

    def test_empty_expected_tools_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationCase(
                case_id="calculator_basic",
                request="Hitung 10 + 20",
                expected_tools=[],
                expected_step_count=1,
                expected_success=True,
                description="Basic calculator task",
            )


if __name__ == "__main__":
    unittest.main()