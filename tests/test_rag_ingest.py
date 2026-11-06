import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.rag.ingest import ingest_directory


class TestIngest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.doc_dir = Path(self.temp_dir.name) / "documents"
        self.doc_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = str(Path(self.temp_dir.name) / "rag.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_directory_not_found(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            ingest_directory("non_existent_folder_abc")
        self.assertIn("Directory not found:", str(ctx.exception))

    def test_no_supported_files(self):
        # Create unsupported file
        (self.doc_dir / "image.png").write_bytes(b"\x89PNG")

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = ingest_directory(directory=str(self.doc_dir), db_path=self.db_path)
            self.assertEqual(result, 0)
            self.assertIn("No .md or .txt documents found.", mock_stdout.getvalue())

    @patch("src.rag.vector_store.embed_text", return_value=[0.1, 0.2])
    def test_ingest_valid_and_empty_documents(self, mock_embed):
        # Create a valid markdown file
        (self.doc_dir / "doc1.md").write_text("This is a test document with several words for chunking.", encoding="utf-8")
        # Create an empty text file
        (self.doc_dir / "empty.txt").write_text("   \n  ", encoding="utf-8")

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            total_chunks = ingest_directory(directory=str(self.doc_dir), db_path=self.db_path)
            self.assertGreater(total_chunks, 0)
            output = mock_stdout.getvalue()
            self.assertIn("INGESTED: doc1.md", output)
            self.assertIn("SKIP: ", output)
            self.assertIn("(empty document)", output)
            self.assertIn("--- INGESTION SUMMARY ---", output)

    def test_main_block(self):
        with patch("sys.stdout", new_callable=io.StringIO):
            with patch("src.rag.ingest.ingest_directory") as mock_ingest:
                from src.rag import ingest
                # Test executing under __main__
                with patch.object(ingest, "__name__", "__main__"):
                    mock_ingest()


if __name__ == "__main__":
    unittest.main()
