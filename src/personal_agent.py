import json
import requests

try:
    from src.memory import Memory
    from src.tools.calculator import calculate
    from src.tools.system_tools import (
        get_current_time,
        list_project_files,
        read_project_file,
    )
except ImportError:
    from memory import Memory
    from tools.calculator import calculate
    from tools.system_tools import (
        get_current_time,
        list_project_files,
        read_project_file,
    )


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:4b"
MAX_TOOL_ROUNDS = 5

memory = Memory()


SYSTEM_PROMPT = """
You are Local Hermes AI, the user's personal AI assistant.

Guidelines:
1. Provide clear and concise answers.
2. Use tools whenever necessary to fulfill tasks.
3. Never make up tool outputs or hallucinate results.
4. For mathematical calculations, use the calculate tool.
5. For current date and time, use get_current_time.
6. To inspect project repository files, use list_project_files.
7. To read a project file's content, use read_project_file.
8. Do not claim to have taken an action if you haven't actually run it.
9. Saved user memory information is provided below.
"""


# Tool definitions for Ollama API
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a mathematical expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression, e.g. 125 * 24"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get current local date, time, and timezone.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_project_files",
            "description": "List files inside the project repository.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_project_file",
            "description": "Read text content of a file in the project repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Relative file path, e.g. README.md"
                    }
                },
                "required": ["filename"]
            }
        }
    }
]


# Map of callable Python functions for tools
AVAILABLE_TOOLS = {
    "calculate": lambda args: calculate(args["expression"]),
    "get_current_time": lambda args: get_current_time(),
    "list_project_files": lambda args: list_project_files(),
    "read_project_file": lambda args: read_project_file(args["filename"]),
}


def execute_tool(tool_name, arguments):
    """Execute the tool selected by the model."""

    if tool_name not in AVAILABLE_TOOLS:
        return {"error": "Unknown tool."}

    try:
        result = AVAILABLE_TOOLS[tool_name](arguments)

        print(f"\n[TOOL] {tool_name} executed successfully.")

        return {"result": result}

    except Exception as error:
        return {"error": str(error)}


def build_messages():
    """Build prompt with conversation history and persistent memory."""

    memories = memory.get_memories()

    memory_text = json.dumps(
        memories,
        ensure_ascii=False,
        indent=2
    )

    system_content = (
        SYSTEM_PROMPT
        + "\n\nSaved user information:\n"
        + memory_text
    )

    return [
        {"role": "system", "content": system_content},
        *memory.get_recent_messages(limit=20)
    ]


def ask_ai(question):
    """Agent decision loop."""

    messages = build_messages()

    messages.append({
        "role": "user",
        "content": question
    })

    for round_number in range(MAX_TOOL_ROUNDS + 1):

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "messages": messages,
                "tools": TOOLS,
                "stream": False
            },
            timeout=(10, 300)
        )

        response.raise_for_status()

        assistant_message = response.json()["message"]

        # Save assistant message, including tool call requests if present
        messages.append(assistant_message)

        tool_calls = assistant_message.get("tool_calls", [])

        # No tool calls means the model produced its final response
        if not tool_calls:
            answer = assistant_message.get("content", "")

            memory.save_message("user", question)
            memory.save_message("assistant", answer)

            return answer

        if round_number == MAX_TOOL_ROUNDS:
            return "Tool usage limit reached. Please try a simpler instruction."

        # Execute all tools requested by the model
        for tool_call in tool_calls:
            function = tool_call["function"]

            tool_name = function["name"]
            arguments = function.get("arguments", {})

            print(f"[AGENT] Selected tool: {tool_name}")

            result = execute_tool(tool_name, arguments)

            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": json.dumps(
                    result,
                    ensure_ascii=False
                )
            })

    return "The agent was unable to fulfill the request."


def main():
    print("=" * 50)
    print("          LOCAL PERSONAL AI AGENT")
    print("=" * 50)

    print("\nSpecial commands:")
    print("/remember key=value")
    print("/memories")
    print("/forget key")
    print("/reset")
    print("/exit")

    print("\nAI is ready!\n")

    try:
        while True:
            question = input("You: ").strip()

            if not question:
                continue

            if question.lower() == "/exit":
                print("AI: Goodbye!")
                break

            if question.lower() == "/memories":
                print(json.dumps(
                    memory.get_memories(),
                    indent=2,
                    ensure_ascii=False
                ))
                continue

            if question == "/remember" or question.startswith("/remember "):
                if question == "/remember":
                    print("Format: /remember key=value")
                    continue

                item = question[len("/remember "):]

                if "=" not in item:
                    print("Format: /remember key=value")
                    continue

                key, value = item.split("=", 1)

                if not key.strip() or not value.strip():
                    print("Key and value cannot be empty.")
                    continue

                memory.remember(key.strip(), value.strip())
                print("AI: Information saved successfully.")
                continue

            if question == "/forget" or question.startswith("/forget "):
                if question == "/forget":
                    print("Format: /forget key")
                    continue

                key = question[len("/forget "):].strip()

                if memory.forget(key):
                    print("AI: Information deleted successfully.")
                else:
                    print("AI: Information not found.")

                continue

            if question.lower() == "/reset":
                memory.clear_history()
                print("AI: Conversation history cleared.")
                continue

            try:
                answer = ask_ai(question)
                print(f"\nAI: {answer}\n")

            except requests.exceptions.RequestException as error:
                print(f"\n[ERROR] Could not connect to Ollama: {error}\n")

            except (KeyError, ValueError, TypeError) as error:
                print(f"\n[ERROR] Invalid response or tool data: {error}\n")

    finally:
        memory.close()


if __name__ == "__main__":
    main()
