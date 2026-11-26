"""Structured logging schema, event taxonomy, correlation, and privacy safeguards."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.automation.logger import _sanitize_details

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}

EVENT_TAXONOMY = {
    "run_started",
    "run_completed",
    "run_failed",
    "task_started",
    "task_completed",
    "task_failed",
    "task_resumed",
    "task_cancelled",
    "step_started",
    "step_completed",
    "step_failed",
    "step_retry",
    "tool_called",
    "tool_completed",
    "tool_failed",
    "approval_requested",
    "approval_granted",
    "approval_denied",
    "retrieval_started",
    "retrieval_completed",
    "retrieval_failed",
    "rag_context_attached",
    "llm_started",
    "llm_completed",
    "llm_failed",
    "evaluation_started",
    "evaluation_completed",
    "evaluation_failed",
    "hermes_request_started",
    "hermes_request_completed",
    "hermes_request_failed",
    "hermes_approval_required",
}

MAX_METADATA_KEYS = 50
MAX_STORED_EVENTS = 10_000


@dataclass(frozen=True)
class StructuredLogRecord:
    timestamp: str
    level: str
    event: str
    run_id: str
    task_id: str | None = None
    step_id: int | None = None
    component: str = "core"
    status: str | None = None
    duration_ms: float | None = None
    error_type: str | None = None
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.timestamp, str) or not self.timestamp.strip():
            raise ValueError("timestamp must be a non-empty string")
        if self.level not in VALID_LOG_LEVELS:
            raise ValueError(f"level must be one of {sorted(VALID_LOG_LEVELS)}")
        if not isinstance(self.event, str) or self.event not in EVENT_TAXONOMY:
            raise ValueError(f"Unknown event in taxonomy: {self.event}")
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if self.step_id is not None and (
            isinstance(self.step_id, bool) or not isinstance(self.step_id, int)
        ):
            raise TypeError("step_id must be an integer or None")
        if self.duration_ms is not None and (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, (int, float))
            or self.duration_ms < 0
        ):
            raise ValueError("duration_ms must be a non-negative number or None")
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary")

        # Enforce metadata size bound and secret redaction
        bounded_items = list(self.metadata.items())[:MAX_METADATA_KEYS]
        sanitized = _sanitize_details(dict(bounded_items))
        object.__setattr__(self, "metadata", sanitized)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "created_at": self.timestamp,
            "level": self.level,
            "event": self.event,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "step_id": self.step_id,
            "component": self.component,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error_type": self.error_type,
            "message": self.message,
            "details": self.metadata,
            "metadata": self.metadata,
        }


class ObservabilityLogger:
    """Best-effort structured logger with correlation IDs, retention bounds, and secret redaction."""

    def __init__(
        self,
        task_logger=None,
        max_events: int = MAX_STORED_EVENTS,
    ):
        if isinstance(max_events, bool) or not isinstance(max_events, int) or max_events <= 0:
            raise ValueError("max_events must be a positive integer")
        self.task_logger = task_logger
        self.max_events = max_events
        self._records: list[dict[str, Any]] = []

    def emit(
        self,
        event: str,
        run_id: str,
        level: str = "INFO",
        task_id: str | None = None,
        step_id: int | None = None,
        component: str = "core",
        status: str | None = None,
        duration_ms: float | None = None,
        error_type: str | None = None,
        message: str = "",
        metadata: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> StructuredLogRecord:
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        record = StructuredLogRecord(
            timestamp=ts,
            level=level,
            event=event,
            run_id=run_id,
            task_id=task_id,
            step_id=step_id,
            component=component,
            status=status,
            duration_ms=duration_ms,
            error_type=error_type,
            message=message,
            metadata=metadata or {},
        )
        record_dict = record.to_dict()

        if len(self._records) >= self.max_events:
            # FIFO retention eviction
            self._records.pop(0)
        self._records.append(record_dict)

        # Best-effort persistence to TaskLogger if configured (never breaks app execution)
        if self.task_logger is not None and task_id:
            try:
                details = {
                    **record.metadata,
                    "run_id": run_id,
                    "level": level,
                    "component": component,
                    "status": status,
                    "duration_ms": duration_ms,
                    "error_type": error_type,
                    "message": message,
                }
                self.task_logger.log_event(
                    task_id=task_id,
                    event=event,
                    step_id=step_id,
                    details=details,
                )
            except Exception:
                pass

        return record

    def get_records(
        self,
        run_id: str | None = None,
        task_id: str | None = None,
        level: str | None = None,
        event: str | None = None,
        error_type: str | None = None,
    ) -> list[dict[str, Any]]:
        results = self._records
        if run_id is not None:
            results = [r for r in results if r.get("run_id") == run_id]
        if task_id is not None:
            results = [r for r in results if r.get("task_id") == task_id]
        if level is not None:
            results = [r for r in results if r.get("level") == level]
        if event is not None:
            results = [r for r in results if r.get("event") == event]
        if error_type is not None:
            results = [r for r in results if r.get("error_type") == error_type]
        return list(results)
