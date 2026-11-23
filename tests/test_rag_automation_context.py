import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.automation.rag_context import (
    ContextChunk,
    RAGConfig,
    RAGContextRetriever,
    RetrievedContext,
)
from src.rag.vector_store import VectorStore


class TestRAGAutomationContext(unittest.TestCase):
    def test_rag_config_validation(self):
        config = RAGConfig(top_k=5, threshold=0.7, max_context_length=2000)
        self.assertEqual(config.top_k, 5)
        self.assertEqual(config.threshold, 0.7)
        self.assertEqual(config.max_context_length, 2000)

        # Invalid top_k
        with self.assertRaises(ValueError):
            RAGConfig(top_k=0)
        with self.assertRaises(TypeError):
            RAGConfig(top_k=2.5)
        with self.assertRaises(TypeError):
            RAGConfig(top_k=True)

        # Invalid threshold
        with self.assertRaises(ValueError):
            RAGConfig(threshold=-0.1)
        with self.assertRaises(ValueError):
            RAGConfig(threshold=1.1)
        with self.assertRaises(TypeError):
            RAGConfig(threshold="0.5")

        # Invalid max_context_length
        with self.assertRaises(ValueError):
            RAGConfig(max_context_length=0)
        with self.assertRaises(TypeError):
            RAGConfig(max_context_length="1000")

    def test_context_chunk_and_retrieved_context_models(self):
        chunk1 = ContextChunk(content="First piece of knowledge", source="doc1.md", score=0.85)
        chunk2 = ContextChunk(content="Second piece of knowledge", source="doc2.md", score=0.75)

        context = RetrievedContext(
            query="test query",
            chunks=[chunk1, chunk2],
        )

        self.assertTrue(context.has_content)
        self.assertEqual(len(context.chunks), 2)
        self.assertEqual(context.sources, ["doc1.md", "doc2.md"])
        self.assertEqual(context.scores, [0.85, 0.75])
        formatted = context.formatted_context()
        self.assertIn("First piece of knowledge", formatted)
        self.assertIn("doc1.md", formatted)
        self.assertIn("doc2.md", formatted)

    def test_empty_retrieved_context(self):
        context = RetrievedContext(query="empty query", chunks=[])
        self.assertFalse(context.has_content)
        self.assertEqual(context.sources, [])
        self.assertEqual(context.scores, [])
        self.assertEqual(context.formatted_context(), "")

    def test_context_truncation_respects_max_context_length(self):
        chunk1 = ContextChunk(content="A" * 600, source="doc1.md", score=0.9)
        chunk2 = ContextChunk(content="B" * 600, source="doc2.md", score=0.8)

        # Max length 1000 characters
        context = RetrievedContext(
            query="long query",
            chunks=[chunk1, chunk2],
            max_length=1000,
        )
        formatted = context.formatted_context()
        self.assertTrue(len(formatted) <= 1000)
        self.assertIn("[TRUNCATED]", formatted)

    def test_retriever_returns_structured_context(self):
        mock_store = MagicMock(spec=VectorStore)
        mock_store.search.return_value = [
            {"content": "Relevant content", "source": "docs/arch.md", "score": 0.88}
        ]

        retriever = RAGContextRetriever(
            vector_store=mock_store,
            config=RAGConfig(top_k=2, threshold=0.6),
        )
        context = retriever.retrieve("What is the architecture?")

        self.assertTrue(context.has_content)
        self.assertEqual(len(context.chunks), 1)
        self.assertEqual(context.chunks[0].content, "Relevant content")
        self.assertEqual(context.chunks[0].source, "docs/arch.md")
        self.assertEqual(context.chunks[0].score, 0.88)
        mock_store.search.assert_called_once_with(
            "What is the architecture?",
            top_k=2,
            threshold=0.6,
        )

    def test_retriever_handles_empty_search_results(self):
        mock_store = MagicMock(spec=VectorStore)
        mock_store.search.return_value = []

        retriever = RAGContextRetriever(
            vector_store=mock_store,
            config=RAGConfig(top_k=3, threshold=0.7),
        )
        context = retriever.retrieve("unknown concept")

        self.assertFalse(context.has_content)
        self.assertEqual(len(context.chunks), 0)

    def test_retriever_failure_semantics(self):
        mock_store = MagicMock(spec=VectorStore)
        mock_store.search.side_effect = RuntimeError("Database locked")

        retriever = RAGContextRetriever(vector_store=mock_store)

        # In non-strict mode (default for planning assist), records error without crashing
        context = retriever.retrieve("some query")
        self.assertFalse(context.has_content)
        self.assertIsNotNone(context.error)
        self.assertIn("Database locked", context.error)

        # In strict mode, raises exception
        with self.assertRaises(RuntimeError):
            retriever.retrieve("some query", strict=True)


if __name__ == "__main__":
    unittest.main()
