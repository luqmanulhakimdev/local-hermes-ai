import unittest

from src.automation.evaluation_cases import EVALUATION_CASES


class TestEvaluationCases(unittest.TestCase):
    def test_dataset_is_not_empty(self):
        self.assertGreater(len(EVALUATION_CASES), 0)

    def test_case_ids_are_unique(self):
        case_ids = [case.case_id for case in EVALUATION_CASES]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_expected_step_count_matches_tool_count(self):
        for case in EVALUATION_CASES:
            self.assertEqual(
                case.expected_step_count,
                len(case.expected_tools),
                case.case_id,
            )

    def test_all_cases_have_required_fields(self):
        for case in EVALUATION_CASES:
            self.assertTrue(case.case_id)
            self.assertTrue(case.request)
            self.assertTrue(case.expected_tools)
            self.assertGreater(case.expected_step_count, 0)
            self.assertIsInstance(case.expected_success, bool)
            self.assertTrue(case.description)


if __name__ == "__main__":
    unittest.main()