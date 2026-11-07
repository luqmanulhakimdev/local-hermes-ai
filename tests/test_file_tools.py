
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.tools import file_tools


class TestFileTools(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.documents = self.root / "documents"
        self.documents.mkdir()

        (self.documents / "example.md").write_text(
            "# Example\nTest content",
            encoding="utf-8",
        )

        self.root_patch = patch.object(
            file_tools, "PROJECT_ROOT", self.root
        )
        self.documents_patch = patch.object(
            file_tools, "DOCUMENTS_DIR", self.documents.resolve()
        )

        self.root_patch.start()
        self.documents_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.documents_patch.stop()
        self.temp_dir.cleanup()

    def test_read_file(self):
        result = file_tools.read_file("documents/example.md")
        self.assertIn("Test content", result)

    def test_list_files(self):
        result = file_tools.list_files("documents")
        self.assertEqual(result, ["documents/example.md"])

    def test_path_outside_documents_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "restricted"):
            file_tools.read_file("../secret.txt")

    def test_unsupported_extension_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Only Markdown"):
            file_tools.read_file("documents/example.py")

    def test_missing_file_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            file_tools.read_file("documents/missing.md")

    def test_symlink_outside_documents_is_rejected(self):
        outside_file = self.root / "secret.md"
        outside_file.write_text("Secret data", encoding="utf-8")

        symlink = self.documents / "external.md"

        try:
            symlink.symlink_to(outside_file)
        except OSError:
            self.skipTest("Symlink is not supported")

        with self.assertRaisesRegex(ValueError, "restricted"):
            file_tools.read_file("documents/external.md")


    def test_list_files_excludes_symlink_outside_documents(self):
        outside_file = self.root / "secret.md"
        outside_file.write_text("Secret data", encoding="utf-8")

        symlink = self.documents / "external.md"

        try:
            symlink.symlink_to(outside_file)
        except OSError:
            self.skipTest("Symlink is not supported")

        result = file_tools.list_files("documents")

        self.assertNotIn("documents/external.md", result)


    def test_oversized_file_is_rejected(self):
        large_file = self.documents / "large.md"
        large_file.write_text(
            "A" * (file_tools.MAX_FILE_SIZE + 1),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "maximum allowed size"):
            file_tools.read_file("documents/large.md")

    def test_read_directory_is_rejected(self):
        with self.assertRaises(ValueError):
            file_tools.read_file("documents")


if __name__ == "__main__":
    unittest.main()
