import unittest
from unittest.mock import patch

from src.rag.retriever import cosine_similarity, retrieve


class TestCosineSimilarity(unittest.TestCase):

    def test_identical_vectors(self):
        result = cosine_similarity(
            [1.0, 0.0],
            [1.0, 0.0],
        )
        self.assertAlmostEqual(result, 1.0)

    def test_orthogonal_vectors(self):
        result = cosine_similarity(
            [1.0, 0.0],
            [0.0, 1.0],
        )
        self.assertAlmostEqual(result, 0.0)

    def test_opposite_vectors(self):
        result = cosine_similarity(
            [1.0, 0.0],
            [-1.0, 0.0],
        )
        self.assertAlmostEqual(result, -1.0)

    def test_dimension_mismatch(self):
        with self.assertRaises(ValueError) as ctx:
            cosine_similarity(
                [1.0, 0.0],
                [1.0, 0.0, 0.0],
            )
        self.assertIn("Vectors must have the same dimension.", str(ctx.exception))

    def test_empty_vector(self):
        with self.assertRaises(ValueError) as ctx:
            cosine_similarity([], [])
        self.assertIn("Vectors cannot be empty.", str(ctx.exception))

    def test_zero_magnitude_vector(self):
        with self.assertRaises(ValueError) as ctx:
            cosine_similarity([0.0, 0.0], [1.0, 2.0])
        self.assertIn("Vectors cannot have zero magnitude.", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            cosine_similarity([1.0, 2.0], [0.0, 0.0])
        self.assertIn("Vectors cannot have zero magnitude.", str(ctx.exception))


class TestRetrieve(unittest.TestCase):

    def test_empty_query_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            retrieve("", ["chunk1"])
        self.assertIn("Query cannot be empty.", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            retrieve("   ", ["chunk1"])
        self.assertIn("Query cannot be empty.", str(ctx.exception))

    def test_empty_chunks_returns_empty_list(self):
        result = retrieve("sample query", [])
        self.assertEqual(result, [])

    def test_invalid_top_k_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            retrieve("sample query", ["chunk1"], top_k=0)
        self.assertIn("top_k must be greater than 0.", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            retrieve("sample query", ["chunk1"], top_k=-1)
        self.assertIn("top_k must be greater than 0.", str(ctx.exception))

    @patch("src.rag.retriever.embed_text")
    def test_retrieve_success_and_ranking(self, mock_embed):
        # Query vector: [1.0, 0.0]
        # Chunk 1 vector: [1.0, 0.0] -> score 1.0
        # Chunk 2 vector: [0.0, 1.0] -> score 0.0
        # Chunk 3 vector: [0.7071, 0.7071] -> score ~0.7071
        def embed_side_effect(text):
            if text == "query":
                return [1.0, 0.0]
            elif text == "chunk1":
                return [1.0, 0.0]
            elif text == "chunk2":
                return [0.0, 1.0]
            elif text == "chunk3":
                return [0.7071, 0.7071]
            return [1.0, 0.0]

        mock_embed.side_effect = embed_side_effect

        results = retrieve("query", ["chunk1", "chunk2", "chunk3"], top_k=2)

        self.assertEqual(len(results), 2)
        # chunk1 should be first with ~1.0
        self.assertEqual(results[0][0], "chunk1")
        self.assertAlmostEqual(results[0][1], 1.0)
        # chunk3 should be second with ~0.7071
        self.assertEqual(results[1][0], "chunk3")
        self.assertAlmostEqual(results[1][1], 0.7071, places=3)


if __name__ == "__main__":
    unittest.main()
