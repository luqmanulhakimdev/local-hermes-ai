
import json
import requests

from src.automation.models import TaskPlan, TaskStep


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"


class TaskPlanner:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        timeout: int = 120,
    ):
        self.model = model
        self.ollama_url = ollama_url.rstrip("/")
        self.timeout = timeout

    def _build_prompt(self, user_request: str) -> str:
        return f"""
You are a task planner for a local AI automation agent.
Convert the user's request into a structured task plan.

Available tools:

1. read_file
   Description: Read a permitted project document.
   Required argument: path

2. list_files
   Description: List permitted documents.
   Optional argument: directory (defaults to "documents")
   Use an empty arguments object if no directory is specified.

3. summarize_text
   Description: Summarize supplied text.
   Required argument: text

4. save_note
   Description: Save a note.
   Required argument: content

5. search_notes
   Description: Search saved notes.
   Required argument: query

6. list_tools
   Description: List all registered automation tools.
   Required arguments: none

Rules:
- Return JSON only. No Markdown code fences.
- Use only the six listed tools.
- Create between 1 and 5 steps.
- Step IDs must be sequential, starting from 1.
- Each step must contain step_id, tool, and arguments.
- Arguments must be a JSON object.
- Use "$step_N" to reference output from a previous step.
- Never reference the current or a future step.
- Do not invent file paths or tool names.
- If the request cannot be completed with these tools,
  return an error field explaining why.
- If the user asks which tools are available, use list_tools.
- If the user asks which documents or files are available, use list_files.
- For read_file followed by summarize_text:
  summarize_text must use {{"text": "$step_1"}}.
- For summarize_text followed by save_note:
  save_note must use {{"content": "$step_2"}}.
- Every step must contain exactly the required fields.
- Do not include extra fields such as reason, explanation, or notes.
- Every step must contain exactly the required fields.
- Do not include extra fields such as reason, explanation, or notes.

IMPORTANT STEP FORMAT:
- The "steps" field must be an array of objects.
- Each step object must have exactly these three keys:
  "step_id", "tool", and "arguments".
- "step_id" must be an integer: 1, 2, 3, etc.
- Never use keys like "step_1", "step_2", or "step_3".
- Never wrap a step inside another object.
- The step_id must be a field, not an object key.

Expected successful response format:
{{
  "description": "Short task description",
  "steps": [
    {{
      "step_id": 1,
      "tool": "read_file",
      "arguments": {{
        "path": "documents/ai-engineering.md"
      }}
    }}
  ]
}}

Example of a valid multi-step response:
{{
  "description": "Read, summarize, and save a document",
  "steps": [
    {{
      "step_id": 1,
      "tool": "read_file",
      "arguments": {{
        "path": "documents/llm-basics.md"
      }}
    }},
    {{
      "step_id": 2,
      "tool": "summarize_text",
      "arguments": {{
        "text": "$step_1"
      }}
    }},
    {{
      "step_id": 3,
      "tool": "save_note",
      "arguments": {{
        "content": "$step_2"
      }}
    }}
  ]
}}

For unsupported requests, return:
{{
  "error": "Explanation of why the request is unsupported"
}}

User request:
{user_request}
""".strip()

    def plan(self, user_request: str) -> TaskPlan:
        if not isinstance(user_request, str) or not user_request.strip():
            raise ValueError("User request must not be empty")

        response = requests.post(
            f"{self.ollama_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You generate structured automation plans. "
                            "Return valid JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_prompt(user_request),
                    },
                ],
                "format": "json",
                "stream": False,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        try:
            content = response.json()["message"]["content"]
            data = json.loads(content)
        except (ValueError, KeyError, TypeError) as error:
            raise ValueError("Planner returned invalid JSON") from error

        if not isinstance(data, dict):
            raise ValueError("Planner response must be a JSON object")

        if data.get("error"):
            raise ValueError(f"Planner cannot create a plan: {data['error']}")

        if set(data.keys()) != {"description", "steps"}:
            raise ValueError(
                "Planner response must contain only description and steps"
            )

        if not isinstance(data["steps"], list):
            raise ValueError("Planner steps must be a list")

        steps = []

        for item in data["steps"]:
            if not isinstance(item, dict):
                raise ValueError("Each step must be a JSON object")

            required_keys = {"step_id", "tool", "arguments"}

            if not required_keys.issubset(item.keys()):
                raise ValueError(
                    f"Invalid step structure. Required: {required_keys}. "
                    f"Received: {set(item.keys())}"
                )

            if not isinstance(item["step_id"], int) or isinstance(item["step_id"], bool):
                raise ValueError("step_id must be an integer")

            if not isinstance(item["tool"], str):
                raise ValueError("tool must be a string")

            if not isinstance(item["arguments"], dict):
                raise ValueError("arguments must be a JSON object")

            steps.append(
                TaskStep(
                    step_id=item["step_id"],
                    tool=item["tool"],
                    arguments=item["arguments"],
                )
            )

        return TaskPlan(
            description=data["description"],
            steps=steps,
        )
