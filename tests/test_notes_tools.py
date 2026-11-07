
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.tools import notes_tools


class TestNotesTools(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)

        self.data_patch = patch.object(
            notes_tools, "DATA_DIR", self.data_dir
        )
        self.db_patch = patch.object(
            notes_tools, "DB_PATH", self.data_dir / "test.db"
        )

        self.data_patch.start()
        self.db_patch.start()

    def tearDown(self):
        self.data_patch.stop()
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_save_note(self):
        result = notes_tools.save_note("Learn AI Engineering")
        self.assertIn("saved successfully", result)

    def test_search_saved_note(self):
        notes_tools.save_note("Learn about local RAG")

        results = notes_tools.search_notes("RAG")

        self.assertEqual(len(results), 1)
        self.assertIn("local RAG", results[0]["content"])

    def test_search_no_match(self):
        notes_tools.save_note("Learn Python")

        results = notes_tools.search_notes("Kubernetes")

        self.assertEqual(results, [])

    def test_empty_note_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            notes_tools.save_note(" ")

    def test_empty_search_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            notes_tools.search_notes(" ")


if __name__ == "__main__":
    unittest.main()
