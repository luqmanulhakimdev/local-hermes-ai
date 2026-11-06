from pathlib import Path
import tempfile
import unittest

from src.rag.chunker import chunk_text, load_document


class TestChunker(unittest.TestCase):

    def test_load_document(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tmp:
            tmp.write("Hello, RAG world!")
            tmp_path = tmp.name

        try:
            content = load_document(tmp_path)
            self.assertEqual(content, "Hello, RAG world!")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_chunk_text_returns_multiple_chunks(self):
        text = "one two three four five six"

        chunks = chunk_text(
            text,
            chunk_size=3,
            overlap=1,
        )

        self.assertGreater(len(chunks), 1)

    def test_chunk_size_is_respected(self):
        text = "one two three four five six"

        chunks = chunk_text(
            text,
            chunk_size=3,
            overlap=1,
        )

        for chunk in chunks:
            self.assertLessEqual(len(chunk.split()), 3)

    def test_empty_or_whitespace_text(self):
        self.assertEqual(chunk_text(""), [])
        self.assertEqual(chunk_text("   \n\t  "), [])

    def test_invalid_chunk_size(self):
        with self.assertRaises(ValueError) as ctx:
            chunk_text(
                "hello world",
                chunk_size=0,
                overlap=0,
            )
        self.assertIn("chunk_size must be greater than 0.", str(ctx.exception))

    def test_negative_overlap(self):
        with self.assertRaises(ValueError) as ctx:
            chunk_text(
                "hello world",
                chunk_size=5,
                overlap=-1,
            )
        self.assertIn("overlap cannot be negative.", str(ctx.exception))

    def test_overlap_greater_equal_chunk_size(self):
        with self.assertRaises(ValueError) as ctx:
            chunk_text(
                "hello world",
                chunk_size=5,
                overlap=5,
            )
        self.assertIn("overlap must be less than chunk_size.", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
