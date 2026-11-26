"""Run-level tracing and lifecycle validation reusing TaskTrace."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.automation.tracing import TaskTrace, build_task_trace


@dataclass(frozen=True)
class SpanTrace:
    name: str
    component: str
    status: str
    start_time: str | None
    end_time: str | None
    duration_ms: float | None
    step_id: int | None = None
    tool: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class RunTrace:
    run_id: str
    task_id: str | None
    status: str
    start_time: str | None
    end_time: str | None
    duration_ms: float | None
    task_trace: TaskTrace | None
    spans: tuple[SpanTrace, ...]
    lifecycle_valid: bool
    lifecycle_errors: tuple[str, ...]


def _parse_ts(ts: Any) -> datetime | None:
    if not isinstance(ts, str) or not ts.strip():
        return None
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def _compute_duration_ms(start_ts: str | None, end_ts: str | None) -> float | None:
    start_dt = _parse_ts(start_ts)
    end_dt = _parse_ts(end_ts)
    if start_dt is None or end_dt is None:
        return None
    diff_ms = (end_dt - start_dt).total_seconds() * 1000.0
    if diff_ms < 0:
        return None
    return round(diff_ms, 3)


def build_run_trace(run_id: str, logs: list[dict[str, Any]]) -> RunTrace:
    """Reconstruct an inspectable RunTrace and validate lifecycle transitions."""
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError("run_id must be a non-empty string")
    if not isinstance(logs, list) or not logs:
        raise ValueError("logs must be a non-empty list")

    lifecycle_errors: list[str] = []
    started_steps: set[int] = set()
    approval_requested_steps: set[int] = set()
    task_failed = False
    task_resumed = False
    run_failed = False

    task_id: str | None = None
    run_start_ts: str | None = None
    run_end_ts: str | None = None
    run_status = "unknown"

    # Track spans for llm, retrieval, and steps
    open_spans: dict[tuple[str, int | None], dict[str, Any]] = {}
    finished_spans: list[SpanTrace] = []

    valid_timestamps: list[tuple[datetime, str]] = []

    for entry in logs:
        if not isinstance(entry, dict):
            continue
        event = entry.get("event", "")
        ts = entry.get("timestamp") or entry.get("created_at")
        dt = _parse_ts(ts)
        if dt is not None and isinstance(ts, str):
            valid_timestamps.append((dt, ts))

        if task_id is None and isinstance(entry.get("task_id"), str) and entry["task_id"].strip():
            task_id = entry["task_id"]

        step_id = entry.get("step_id")
        details = entry.get("details") or entry.get("metadata") or {}
        if not isinstance(details, dict):
            details = {}
        component = entry.get("component") or details.get("component") or "core"

        if event == "run_started":
            run_start_ts = ts
            run_status = "running"
        elif event == "run_completed":
            if run_failed:
                lifecycle_errors.append("run_completed observed after run_failed")
            run_end_ts = ts
            run_status = "completed"
        elif event == "run_failed":
            run_failed = True
            run_end_ts = ts
            run_status = "failed"
        elif event == "task_started":
            if run_status == "unknown":
                run_status = "running"
        elif event == "task_resumed":
            task_resumed = True
            task_failed = False
        elif event == "task_failed":
            task_failed = True
            if run_status in {"unknown", "running"}:
                run_status = "failed"
        elif event == "task_completed":
            if task_failed and not task_resumed:
                lifecycle_errors.append("task_completed observed after task_failed without resume")
            if run_status in {"unknown", "running"}:
                run_status = "completed"

        # Step lifecycle
        elif event == "step_started" and step_id is not None:
            started_steps.add(step_id)
            open_spans[("step", step_id)] = {
                "name": f"step_{step_id}",
                "component": "executor",
                "start_time": ts,
                "step_id": step_id,
                "tool": details.get("tool"),
            }
        elif event in {"step_completed", "step_failed"} and step_id is not None:
            if step_id not in started_steps:
                lifecycle_errors.append(f"{event} observed for step {step_id} without step_started")
            span_info = open_spans.pop(("step", step_id), None)
            start_t = span_info["start_time"] if span_info else None
            dur = entry.get("duration_ms")
            if dur is None:
                dur = _compute_duration_ms(start_t, ts)
            finished_spans.append(
                SpanTrace(
                    name=f"step_{step_id}",
                    component="executor",
                    status="completed" if event == "step_completed" else "failed",
                    start_time=start_t,
                    end_time=ts,
                    duration_ms=dur,
                    step_id=step_id,
                    tool=details.get("tool") or (span_info["tool"] if span_info else None),
                    error=details.get("error"),
                )
            )

        # Approval lifecycle
        elif event == "approval_requested" and step_id is not None:
            approval_requested_steps.add(step_id)
            open_spans[("approval", step_id)] = {
                "name": f"approval_step_{step_id}",
                "component": "approval",
                "start_time": ts,
                "step_id": step_id,
                "tool": details.get("tool"),
            }
        elif event in {"approval_granted", "approval_denied"} and step_id is not None:
            if step_id not in approval_requested_steps:
                lifecycle_errors.append(
                    f"{event} observed for step {step_id} without approval_requested"
                )
            span_info = open_spans.pop(("approval", step_id), None)
            start_t = span_info["start_time"] if span_info else None
            dur = entry.get("duration_ms")
            if dur is None:
                dur = _compute_duration_ms(start_t, ts)
            finished_spans.append(
                SpanTrace(
                    name=f"approval_step_{step_id}",
                    component="approval",
                    status="granted" if event == "approval_granted" else "denied",
                    start_time=start_t,
                    end_time=ts,
                    duration_ms=dur,
                    step_id=step_id,
                    tool=details.get("tool") or (span_info["tool"] if span_info else None),
                )
            )

        # LLM / Retrieval / Tool spans
        elif event in {"llm_started", "retrieval_started", "tool_called"}:
            kind = event.split("_")[0]
            open_spans[(kind, step_id)] = {
                "name": kind,
                "component": component,
                "start_time": ts,
                "step_id": step_id,
                "tool": details.get("tool"),
            }
        elif event in {
            "llm_completed",
            "llm_failed",
            "retrieval_completed",
            "retrieval_failed",
            "tool_completed",
            "tool_failed",
        }:
            kind = event.split("_")[0]
            span_info = open_spans.pop((kind, step_id), None)
            start_t = span_info["start_time"] if span_info else None
            dur = entry.get("duration_ms")
            if dur is None:
                dur = _compute_duration_ms(start_t, ts)
            finished_spans.append(
                SpanTrace(
                    name=kind,
                    component=component,
                    status="completed" if event.endswith("completed") else "failed",
                    start_time=start_t,
                    end_time=ts,
                    duration_ms=dur,
                    step_id=step_id,
                    tool=details.get("tool") or (span_info["tool"] if span_info else None),
                    error=details.get("error") or entry.get("error_type"),
                )
            )

    # Compute total run duration only from valid timestamps
    if run_start_ts is None and valid_timestamps:
        run_start_ts = valid_timestamps[0][1]
    if run_end_ts is None and len(valid_timestamps) >= 2:
        run_end_ts = valid_timestamps[-1][1]

    total_duration_ms = _compute_duration_ms(run_start_ts, run_end_ts)

    task_trace = None
    if task_id is not None:
        task_logs = [e for e in logs if isinstance(e, dict) and e.get("task_id")]
        if task_logs:
            try:
                task_trace = build_task_trace(task_logs)
            except Exception:
                task_trace = None

    return RunTrace(
        run_id=run_id,
        task_id=task_id,
        status=run_status,
        start_time=run_start_ts,
        end_time=run_end_ts,
        duration_ms=total_duration_ms,
        task_trace=task_trace,
        spans=tuple(finished_spans),
        lifecycle_valid=len(lifecycle_errors) == 0,
        lifecycle_errors=tuple(lifecycle_errors),
    )
