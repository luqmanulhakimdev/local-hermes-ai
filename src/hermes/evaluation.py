"""Observability and evaluation metrics for Hermes integration runs."""

from dataclasses import dataclass
from typing import Any

from src.hermes.protocol import HermesRequest, HermesRequestStatus, HermesResponse


@dataclass(frozen=True)
class HermesRunMetrics:
    request_id: str
    operation: str
    hermes_request_success: bool
    hermes_adapter_success: bool
    hermes_to_automation_success: bool | None
    hermes_to_rag_success: bool | None
    approval_compliance: bool | None
    trace_complete: bool | None
    recovery_success: bool | None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")
        if not isinstance(self.operation, str) or not self.operation.strip():
            raise ValueError("operation must be a non-empty string")
        if not isinstance(self.hermes_request_success, bool):
            raise ValueError("hermes_request_success must be a boolean")
        if not isinstance(self.hermes_adapter_success, bool):
            raise ValueError("hermes_adapter_success must be a boolean")
        if self.hermes_to_automation_success is not None and not isinstance(
            self.hermes_to_automation_success, bool
        ):
            raise ValueError("hermes_to_automation_success must be a boolean or None")
        if self.hermes_to_rag_success is not None and not isinstance(
            self.hermes_to_rag_success, bool
        ):
            raise ValueError("hermes_to_rag_success must be a boolean or None")
        if self.approval_compliance is not None and not isinstance(
            self.approval_compliance, bool
        ):
            raise ValueError("approval_compliance must be a boolean or None")
        if self.trace_complete is not None and not isinstance(
            self.trace_complete, bool
        ):
            raise ValueError("trace_complete must be a boolean or None")
        if self.recovery_success is not None and not isinstance(
            self.recovery_success, bool
        ):
            raise ValueError("recovery_success must be a boolean or None")


def evaluate_hermes_run(
    request: HermesRequest,
    response: HermesResponse,
    logs: list[dict[str, Any]] | None = None,
) -> HermesRunMetrics:
    """Analyze a completed Hermes request/response cycle and produce deterministic metrics."""
    hermes_request_success = response.status == HermesRequestStatus.COMPLETED
    hermes_adapter_success = response.status in {
        HermesRequestStatus.COMPLETED,
        HermesRequestStatus.AWAITING_APPROVAL,
        HermesRequestStatus.FAILED,
        HermesRequestStatus.REJECTED,
    }

    hermes_to_automation = None
    if request.operation == "run_automation":
        hermes_to_automation = response.status == HermesRequestStatus.COMPLETED

    hermes_to_rag = None
    if request.operation == "query_knowledge":
        hermes_to_rag = response.status == HermesRequestStatus.COMPLETED

    trace_complete = None
    if logs is not None:
        events = [log.get("event") for log in logs]
        has_start = "hermes_request_started" in events
        has_end = (
            "hermes_request_completed" in events
            or "hermes_request_failed" in events
            or "hermes_approval_required" in events
            or "task_completed" in events
            or "task_failed" in events
        )
        trace_complete = has_start and has_end

    return HermesRunMetrics(
        request_id=request.request_id,
        operation=request.operation,
        hermes_request_success=hermes_request_success,
        hermes_adapter_success=hermes_adapter_success,
        hermes_to_automation_success=hermes_to_automation,
        hermes_to_rag_success=hermes_to_rag,
        approval_compliance=True if response.status != HermesRequestStatus.REJECTED else None,
        trace_complete=trace_complete,
        recovery_success=None,
    )
