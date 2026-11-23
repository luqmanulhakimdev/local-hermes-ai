from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    request: str
    expected_tools: list[str]
    expected_step_count: int
    expected_success: bool
    description: str

    def __post_init__(self):
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ValueError("case_id must not be empty")

        if not isinstance(self.request, str) or not self.request.strip():
            raise ValueError("request must not be empty")

        if not isinstance(self.expected_tools, list) or not self.expected_tools:
            raise ValueError("expected_tools must not be empty")

        if any(
            not isinstance(tool, str) or not tool.strip()
            for tool in self.expected_tools
        ):
            raise ValueError(
                "expected_tools must contain non-empty strings"
            )

        if (
            not isinstance(self.expected_step_count, int)
            or isinstance(self.expected_step_count, bool)
        ):
            raise ValueError(
                "expected_step_count must be an integer"
            )

        if self.expected_step_count < 1:
            raise ValueError(
                "expected_step_count must be greater than 0"
            )

        if not isinstance(self.expected_success, bool):
            raise ValueError(
                "expected_success must be a boolean"
            )

        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError(
                "description must not be empty"
            )