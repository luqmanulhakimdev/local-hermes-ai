from src.automation.registry import ToolDefinition, ToolRegistry
from src.tools.file_tools import read_file, list_files
from src.tools.text_tools import summarize_text
from src.tools.notes_tools import save_note, search_notes


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    tools = [
        ToolDefinition(
            "read_file",
            "Read a permitted project document",
            read_file,
            {"path"},
        ),
        ToolDefinition(
            "list_files",
            "List permitted documents",
            list_files,
            set(),
        ),
        ToolDefinition(
            "list_tools",
            "List all registered automation tools",
            lambda: registry.list_tools(),
            set(),
        ),
        ToolDefinition(
            "summarize_text",
            "Summarize supplied text",
            summarize_text,
            {"text"},
        ),
        ToolDefinition(
            "save_note",
            "Save a note",
            save_note,
            {"content"},
        ),
        ToolDefinition(
            "search_notes",
            "Search saved notes",
            search_notes,
            {"query"},
        ),
    ]

    for tool in tools:
        registry.register(tool)

    return registry