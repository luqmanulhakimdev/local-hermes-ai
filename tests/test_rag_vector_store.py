from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.rag.vector_store import VectorStore


class TestVectorStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_rag.db")
        self.store = VectorStore(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_chunks_empty_source_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.store.add_chunks(["some text"], "")
        self.assertIn("Source cannot be empty.", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.store.add_chunks(["some text"], "   ")
        self.assertIn("Source cannot be empty.", str(ctx.exception))

    @patch("src.rag.vector_store.embed_text")
    def test_add_and_search_chunks(self, mock_embed):
        def mock_embed_fn(text):
            if "python" in text.lower():
                return [1.0, 0.0]
            elif "rust" in text.lower():
                return [0.0, 1.0]
            return [0.5, 0.5]

        mock_embed.side_effect = mock_embed_fn

        chunks = ["Python is awesome", "Rust is fast", "   "]  # empty chunk should be skipped
        self.store.add_chunks(chunks, "doc1.md")

        results = self.store.search("python language", top_k=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["content"], "Python is awesome")
        self.assertEqual(results[0]["source"], "doc1.md")
        self.assertAlmostEqual(results[0]["score"], 1.0)

    @patch("src.rag.vector_store.embed_text")
    def test_add_chunks_replaces_existing_source(self, mock_embed):
        mock_embed.return_value = [1.0, 0.0]

        self.store.add_chunks(["Old chunk 1", "Old chunk 2"], "same_source.md")
        self.store.add_chunks(["New chunk"], "same_source.md")

        results = self.store.search("query", top_k=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "New chunk")

    def test_search_empty_query_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.store.search("")
        self.assertIn("Query cannot be empty.", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.store.search("   ")
        self.assertIn("Query cannot be empty.", str(ctx.exception))

    def test_search_invalid_top_k_raises_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.store.search("valid query", top_k=0)
        self.assertIn("top_k must be greater than 0.", str(ctx.exception))

    @patch("src.rag.vector_store.embed_text")
    def test_search_threshold_filtering(self, mock_embed):
        def mock_embed_fn(text):
            if text == "query":
                return [1.0, 0.0]
            elif text == "high":
                return [1.0, 0.0]  # score 1.0
            elif text == "low":
                return [0.0, 1.0]  # score 0.0
            return [0.0, 0.0]

        mock_embed.side_effect = mock_embed_fn

        self.store.add_chunks(["high", "low"], "doc.md")

        # Threshold at 0.5 should only return "high"
        results = self.store.search("query", top_k=5, threshold=0.5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "high")


if __name__ == "__main__":
    unittest.main()

