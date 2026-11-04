from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools.system_tools import (
    get_current_time,
    list_project_files,
    read_project_file,
)


class TestSystemTools(unittest.TestCase):
    def test_get_current_time(self):
        result = get_current_time()
        self.assertIsInstance(result, dict)
        self.assertIn("date", result)
        self.assertIn("time", result)
        self.assertIn("timezone", result)
        self.assertEqual(len(result["date"].split("-")), 3)

    def test_list_project_files(self):
        files = list_project_files()
        self.assertIsInstance(files, list)
        self.assertTrue(len(files) > 0)

        for filepath in files:
            parts = Path(filepath).parts
            self.assertNotIn(".git", parts)
            self.assertNotIn(".venv", parts)
            self.assertNotIn("__pycache__", parts)
            self.assertNotIn(".env", parts)

    def test_list_project_files_max_limit(self):
        mock_paths = [Path(PROJECT_ROOT / f"dummy_{i}.txt") for i in range(150)]
        with patch.object(Path, "rglob", return_value=mock_paths):
            with patch.object(Path, "is_file", return_value=True):
                files = list_project_files()
                self.assertLessEqual(len(files), 100)

    def test_read_project_file_success(self):
        content = read_project_file("requirements.txt")
        self.assertIsInstance(content, str)
        self.assertIn("requests", content)

    def test_read_project_file_traversal_denied(self):
        with self.assertRaises(ValueError) as ctx:
            read_project_file("../../etc/passwd")
        self.assertIn("Access outside the project root is denied.", str(ctx.exception))

    def test_read_project_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            read_project_file("non_existent_file_12345.txt")
        self.assertIn("File not found.", str(ctx.exception))

    def test_read_project_file_too_large(self):
        with tempfile.NamedTemporaryFile(dir=PROJECT_ROOT, suffix=".txt") as temp_file:
            temp_path = Path(temp_file.name)
            relative_name = temp_path.name
            # Write 100,001 bytes
            temp_file.write(b"a" * 100_001)
            temp_file.flush()

            with self.assertRaises(ValueError) as ctx:
                read_project_file(relative_name)
            self.assertIn("File is too large to read.", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

