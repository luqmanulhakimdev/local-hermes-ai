
import unittest

from src.automation.registry import ToolDefinition, ToolRegistry


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="greet",
                description="Return a greeting",
                handler=lambda name: f"Hello, {name}!",
                required_arguments={"name"},
            )
        )

    def test_registered_tool_can_execute(self):
        result = self.registry.execute(
            "greet",
            {"name": "AI Engineer"},
        )

        self.assertEqual(result, "Hello, AI Engineer!")

    def test_unknown_tool_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Tool is not allowed"):
            self.registry.execute("delete_file", {})

    def test_missing_argument_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Missing required arguments"):
            self.registry.execute("greet", {})

    def test_duplicate_tool_registration_is_rejected(self):
        tool = ToolDefinition(
            name="greet",
            description="Duplicate greeting",
            handler=lambda: "Hi",
            required_arguments=set(),
        )

        with self.assertRaisesRegex(ValueError, "already registered"):
            self.registry.register(tool)

    def test_list_tools(self):
        self.assertEqual(self.registry.list_tools(), ["greet"])

    def test_unexpected_argument_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unexpected arguments"):
            self.registry.execute(
                "greet",
                {
                    "name": "AI Engineer",
                    "delete_all": True,
                },
            )


    def test_invalid_arguments_do_not_execute_handler(self):
        executed = []

        self.registry.register(
            ToolDefinition(
                name="tracked",
                description="Track handler execution",
                handler=lambda name: executed.append(name),
                required_arguments={"name"},
            )
        )

        with self.assertRaises(ValueError):
            self.registry.execute(
                "tracked",
                {
                    "name": "Hermes",
                    "unexpected": True,
                },
            )

        self.assertEqual(executed, [])


    def test_non_dictionary_arguments_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be a dictionary"):
            self.registry.execute("greet", ["AI Engineer"])


if __name__ == "__main__":
    unittest.main()
