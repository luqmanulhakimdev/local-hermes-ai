import unittest

from src.evaluation.golden_dataset import (
    DEFAULT_GOLDEN_DATASET,
    GoldenCase,
    GoldenDataset,
)


class TestGoldenDataset(unittest.TestCase):
    def test_default_dataset_is_valid_and_covers_all_categories(self):
        self.assertEqual(DEFAULT_GOLDEN_DATASET.version, "1.0.0")
        self.assertGreaterEqual(len(DEFAULT_GOLDEN_DATASET.cases), 18)

        for cat in ("llm", "rag", "automation", "security"):
            self.assertGreater(
                len(DEFAULT_GOLDEN_DATASET.filter_by_category(cat)),
                0,
                f"Expected cases for category {cat}",
            )

        self.assertIsNotNone(DEFAULT_GOLDEN_DATASET.get_case("llm_factual_basic"))
        self.assertIsNone(DEFAULT_GOLDEN_DATASET.get_case("nonexistent"))

    def test_duplicate_case_ids_rejected(self):
        c1 = GoldenCase(case_id="dup", category="llm", input_text="Hello")
        c2 = GoldenCase(case_id="dup", category="llm", input_text="World")
        with self.assertRaises(ValueError) as ctx:
            GoldenDataset(name="test", version="1.0", cases=(c1, c2))
        self.assertIn("Duplicate case_id", str(ctx.exception))

    def test_malformed_cases_rejected(self):
        with self.assertRaises(ValueError):
            GoldenCase(case_id="", category="llm", input_text="Hi")
        with self.assertRaises(ValueError):
            GoldenCase(case_id="id1", category="invalid", input_text="Hi")
        with self.assertRaises(ValueError):
            GoldenCase(case_id="id1", category="llm", input_text="   ")
        with self.assertRaises(ValueError):
            GoldenCase(
                case_id="id1",
                category="automation",
                input_text="Run",
                expected_tools=["calculator"],
                expected_step_count=2,
            )
        with self.assertRaises(ValueError):
            GoldenCase(
                case_id="id1",
                category="llm",
                input_text="Hi",
                metadata="not_a_dict",  # type: ignore
            )

    def test_empty_dataset_rejected(self):
        with self.assertRaises(ValueError):
            GoldenDataset(name="empty", version="1.0", cases=())


if __name__ == "__main__":
    unittest.main()
