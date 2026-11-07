
import unittest

from src.automation.tool_setup import create_tool_registry


class TestToolSetup(unittest.TestCase):

    def test_expected_tools_are_registered(self):
        registry = create_tool_registry()

        self.assertEqual(
            registry.list_tools(),
            [
                "list_files",
                "list_tools",
                "read_file",
                "save_note",
                "search_notes",
                "summarize_text",
            ],
        )


if __name__ == "__main__":
    unittest.main()
