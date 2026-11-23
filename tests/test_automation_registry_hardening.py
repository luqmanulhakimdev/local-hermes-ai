import unittest

from src.automation.registry import ToolDefinition, ToolRegistry


class TestRegistryHardening(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()

    def test_invalid_handler_rejected(self):
        with self.assertRaises(TypeError):
            ToolDefinition(
                name="tool",
                description="desc",
                handler="not_callable",
                required_arguments=set(),
            )

    def test_invalid_name_rejected(self):
        with self.assertRaises(ValueError):
            ToolDefinition(
                name="",
                description="desc",
                handler=lambda: "ok",
                required_arguments=set(),
            )
        with self.assertRaises(ValueError):
            ToolDefinition(
                name="   ",
                description="desc",
                handler=lambda: "ok",
                required_arguments=set(),
            )
        with self.assertRaises(TypeError):
            ToolDefinition(
                name=123,
                description="desc",
                handler=lambda: "ok",
                required_arguments=set(),
            )

    def test_invalid_description_rejected(self):
        with self.assertRaises(ValueError):
            ToolDefinition(
                name="tool",
                description="",
                handler=lambda: "ok",
                required_arguments=set(),
            )
        with self.assertRaises(TypeError):
            ToolDefinition(
                name="tool",
                description=123,
                handler=lambda: "ok",
                required_arguments=set(),
            )

    def test_invalid_required_arguments_rejected(self):
        with self.assertRaises(TypeError):
            ToolDefinition(
                name="tool",
                description="desc",
                handler=lambda: "ok",
                required_arguments=["not_a_set"],
            )

    def test_invalid_requires_approval_rejected(self):
        tool = ToolDefinition(
            name="tool",
            description="desc",
            handler=lambda: "ok",
            required_arguments=set(),
            requires_approval="true",
        )
        with self.assertRaises(ValueError):
            tool.validate_arguments({})

    def test_duplicate_registration_rejected(self):
        tool = ToolDefinition(
            name="unique_tool",
            description="desc",
            handler=lambda: "ok",
            required_arguments=set(),
        )
        self.registry.register(tool)
        with self.assertRaises(ValueError) as ctx:
            self.registry.register(tool)
        self.assertIn("already registered", str(ctx.exception))

    def test_get_unknown_tool_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            self.registry.get("non_existent_tool")
        self.assertIn("not allowed", str(ctx.exception))

    def test_get_empty_tool_name_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.get("")
        with self.assertRaises(ValueError):
            self.registry.get("   ")
        with self.assertRaises(TypeError):
            self.registry.get(None)

    def test_argument_validation(self):
        tool = ToolDefinition(
            name="arg_tool",
            description="desc",
            handler=lambda x: x,
            required_arguments={"x"},
        )
        # Missing argument
        with self.assertRaises(ValueError) as ctx:
            tool.validate_arguments({})
        self.assertIn("Missing required arguments: x", str(ctx.exception))

        # Unexpected argument
        with self.assertRaises(ValueError) as ctx:
            tool.validate_arguments({"x": 1, "y": 2})
        self.assertIn("Unexpected arguments: y", str(ctx.exception))

        # Invalid arguments type
        with self.assertRaises(ValueError):
            tool.validate_arguments(["not", "a", "dict"])


if __name__ == "__main__":
    unittest.main()
