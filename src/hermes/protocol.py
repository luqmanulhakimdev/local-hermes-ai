"""Structured request and response protocol for Hermes integration."""

from dataclasses import dataclass, field
from typing import Any

from src.hermes.errors import InvalidRequestError


class HermesRequestStatus:
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    AWAITING_APPROVAL = "awaiting_approval"
    FAILED = "failed"
    REJECTED = "rejected"

    ALL = {ACCEPTED, COMPLETED, AWAITING_APPROVAL, FAILED, REJECTED}


VALID_OPERATIONS = {
    "run_automation",
    "query_knowledge",
    "get_task_status",
    "resume_task",
}


@dataclass(frozen=True)
class HermesRequest:
    request_id: str
    operation: str
    message: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise InvalidRequestError("request_id must be a non-empty string")

        if not isinstance(self.operation, str) or self.operation not in VALID_OPERATIONS:
            raise InvalidRequestError(
                f"operation must be one of {sorted(VALID_OPERATIONS)}, got: {self.operation}"
            )

        if not isinstance(self.message, str) or not self.message.strip():
            raise InvalidRequestError("message must be a non-empty string")

        if not isinstance(self.arguments, dict):
            raise InvalidRequestError("arguments must be a dictionary")


@dataclass(frozen=True)
class HermesResponse:
    request_id: str
    status: str
    message: str
    task_id: str | None = None
    data: Any = None
    error: str | None = None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")

        if self.status not in HermesRequestStatus.ALL:
            raise ValueError(
                f"status must be one of {sorted(HermesRequestStatus.ALL)}, got: {self.status}"
            )

        if not isinstance(self.message, str):
            raise ValueError("message must be a string")
