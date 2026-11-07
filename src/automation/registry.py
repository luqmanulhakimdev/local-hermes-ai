
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: Callable[..., Any]
    required_arguments: set[str]

    def validate_arguments(self, arguments: dict) -> None:
        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a dictionary")

        missing = self.required_arguments - arguments.keys()

        if missing:
            raise ValueError(
                f"Missing required arguments: {', '.join(sorted(missing))}"
            )

        unexpected = arguments.keys() - self.required_arguments

        if unexpected:
            raise ValueError(
                f"Unexpected arguments: {', '.join(sorted(unexpected))}"
            )


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if not isinstance(tool, ToolDefinition):
            raise TypeError("tool must be a ToolDefinition")

        if not tool.name or not tool.name.strip():
            raise ValueError("Tool name must not be empty")

        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        tool = self._tools.get(name)

        if tool is None:
            raise ValueError(f"Tool is not allowed: {name}")

        return tool

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def execute(self, name: str, arguments: dict) -> Any:
        tool = self.get(name)
        tool.validate_arguments(arguments)

        return tool.handler(**arguments)
