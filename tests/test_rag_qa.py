import unittest
from unittest.mock import patch

from src.rag.qa import answer_question


class TestRAGQA(unittest.TestCase):

    @patch("src.rag.qa.VectorStore")
    def test_no_relevant_context(self, mock_vector_store):
        mock_vector_store.return_value.search.return_value = []

        result = answer_question("What is the capital of Japan?")

        self.assertEqual(
            result,
            "No relevant information found.",
        )

    @patch("src.rag.qa.requests.post")
    @patch("src.rag.qa.VectorStore")
    def test_answer_uses_retrieved_context(
        self,
        mock_vector_store,
        mock_post,
    ):
        mock_vector_store.return_value.search.return_value = [
            {
                "content": "A token is a small unit of text.",
                "score": 0.80,
                "source": "llm-basics.md",
            }
        ]

        mock_post.return_value.json.return_value = {
            "message": {
                "content": "A token is a small unit of text."
            }
        }

        mock_post.return_value.raise_for_status.return_value = None

        result = answer_question("What is a token?")

        self.assertIn(
            "A token is a small unit of text.",
            result,
        )
        self.assertIn("llm-basics.md", result)

        mock_post.assert_called_once()

    def test_empty_question_raises_value_error(self):
        with self.assertRaises(ValueError):
            answer_question("   ")


if __name__ == "__main__":
    unittest.main()
