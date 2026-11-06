import io
import unittest
from unittest.mock import MagicMock, patch

from src.rag.evaluation import (
    evaluate_answer_quality,
    evaluate_negative_answers,
    evaluate_retrieval,
    keyword_coverage,
    main,
    print_retrieval_results,
)


class TestRAGEvaluation(unittest.TestCase):

    def test_keyword_coverage(self):
        # Full coverage
        score = keyword_coverage("A token is a small unit of text", ["token", "unit"])
        self.assertEqual(score, 1.0)

        # Partial coverage
        score = keyword_coverage("A token is small", ["token", "unit"])
        self.assertEqual(score, 0.5)

        # Zero coverage
        score = keyword_coverage("Nothing matches here", ["alpha", "beta"])
        self.assertEqual(score, 0.0)

        # Empty keywords
        score = keyword_coverage("Any answer", [])
        self.assertEqual(score, 1.0)

    def test_evaluate_retrieval_invalid_top_k(self):
        mock_store = MagicMock()
        with self.assertRaises(ValueError) as ctx:
            evaluate_retrieval(mock_store, [], top_k=0)
        self.assertIn("top_k must be greater than 0.", str(ctx.exception))

    def test_evaluate_retrieval_matching_and_negative_cases(self):
        mock_store = MagicMock()

        def mock_search(query, top_k=3, threshold=0.65):
            if "positive" in query:
                return [
                    {"source": "doc1.md", "score": 0.85},
                    {"source": "doc2.md", "score": 0.75},
                ]
            else:
                return []

        mock_store.search.side_effect = mock_search

        test_cases = [
            {
                "question": "positive query",
                "expected_sources": ["doc1.md"],
            },
            {
                "question": "negative query",
                "expected_sources": [],
            },
            {
                "question": "missed query",
                "expected_sources": ["doc3.md"],
            },
        ]

        results = evaluate_retrieval(mock_store, test_cases, top_k=3)

        self.assertEqual(len(results), 3)

        # Case 1: retrieved doc1 and doc2, expected doc1
        # Relevant: {doc1}, Precision = 1/2 = 0.5, Recall = 1/1 = 1.0
        self.assertEqual(results[0]["precision"], 0.5)
        self.assertEqual(results[0]["recall"], 1.0)

        # Case 2: retrieved [], expected [] -> precision=1.0, recall=1.0
        self.assertEqual(results[1]["precision"], 1.0)
        self.assertEqual(results[1]["recall"], 1.0)

        # Case 3: missed query: retrieved [], expected doc3 -> precision=0.0, recall=0.0
        self.assertEqual(results[2]["precision"], 0.0)
        self.assertEqual(results[2]["recall"], 0.0)

    @patch("src.rag.evaluation.answer_question")
    def test_evaluate_answer_quality(self, mock_answer):
        mock_answer.return_value = "A token is a small unit of text."
        test_cases = [
            {
                "question": "What is a token?",
                "expected_source": "llm-basics.md",
                "expected_keywords": ["token", "unit"],
            }
        ]

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            results = evaluate_answer_quality(test_cases=test_cases)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["keyword_coverage"], 1.0)
            self.assertIn("ANSWER QUALITY EVALUATION", mock_stdout.getvalue())

    @patch("src.rag.evaluation.answer_question")
    def test_evaluate_negative_answers(self, mock_answer):
        mock_answer.side_effect = [
            "No relevant information found.",
            "I invent an answer here.",
        ]

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            results = evaluate_negative_answers(negative_cases=["Q1", "Q2"])
            self.assertEqual(len(results), 2)
            self.assertTrue(results[0]["passed"])
            self.assertFalse(results[1]["passed"])
            self.assertIn("Passed: 1/2", mock_stdout.getvalue())

    def test_print_retrieval_results(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_retrieval_results([])
            self.assertIn("RETRIEVAL EVALUATION", mock_stdout.getvalue())

        sample_results = [
            {
                "question": "What is AI?",
                "expected_sources": ["ai.md"],
                "retrieved_sources": ["ai.md"],
                "precision": 1.0,
                "recall": 1.0,
                "retrieved_details": [{"source": "ai.md", "score": 0.95}],
            }
        ]
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_retrieval_results(sample_results)
            output = mock_stdout.getvalue()
            self.assertIn("What is AI?", output)
            self.assertIn("Average Precision@3: 1.00", output)

    @patch("src.rag.evaluation.evaluate_negative_answers")
    @patch("src.rag.evaluation.evaluate_answer_quality")
    @patch("src.rag.evaluation.print_retrieval_results")
    @patch("src.rag.evaluation.evaluate_retrieval")
    @patch("src.rag.evaluation.VectorStore")
    def test_main(self, mock_vs, mock_eval_ret, mock_print_ret, mock_eval_ans, mock_eval_neg):
        main()
        mock_vs.assert_called_once()
        mock_eval_ret.assert_called_once()
        mock_print_ret.assert_called_once()
        mock_eval_ans.assert_called_once()
        mock_eval_neg.assert_called_once()


if __name__ == "__main__":
    unittest.main()

