from dataclasses import dataclass, field
from typing import Any


@dataclass
class StepTrace:
    step_id: int
    tool: str | None = None
    arguments: dict | None = None
    started: bool = False
    completed: bool = False
    failed: bool = False
    error: str | None = None
    output: Any = None
    approval_requested: bool = False
    approval_granted: bool = False
    approval_denied: bool = False
    events: list[str] = field(default_factory=list)


@dataclass
class TaskTrace:
    task_id: str
    description: str | None = None
    started: bool = False
    completed: bool = False
    failed: bool = False
    resumed: bool = False
    error: str | None = None
    steps: dict[int, StepTrace] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

    @classmethod
    def from_logs(cls, logs: list[dict]) -> "TaskTrace":
        if not isinstance(logs, list):
            raise TypeError("logs must be a list")

        if not logs:
            raise ValueError("logs must not be empty")

        for log in logs:
            if not isinstance(log, dict):
                raise TypeError("log entries must be dictionaries")

        task_id = logs[0].get("task_id")
        if not task_id or not isinstance(task_id, str):
            raise ValueError("log entries must contain a valid task_id")

        for log in logs:
            if log.get("task_id") != task_id:
                raise ValueError("all log entries must belong to the same task_id")

        trace = cls(task_id=task_id)

        for log in logs:
            event = log.get("event")
            step_id = log.get("step_id")
            details = log.get("details") or {}

            trace.events.append(event)

            if event == "task_started":
                trace.started = True
                trace.description = details.get("description")
            elif event == "task_resumed":
                trace.resumed = True
            elif event == "task_completed":
                trace.completed = True
            elif event == "task_failed":
                trace.failed = True
                trace.error = details.get("error")

            if step_id is not None:
                if step_id not in trace.steps:
                    trace.steps[step_id] = StepTrace(step_id=step_id)

                step_trace = trace.steps[step_id]
                step_trace.events.append(event)

                if event == "step_started":
                    step_trace.started = True
                    step_trace.tool = details.get("tool")
                    step_trace.arguments = details.get("arguments")
                elif event == "approval_requested":
                    step_trace.approval_requested = True
                    if not step_trace.tool:
                        step_trace.tool = details.get("tool")
                    if not step_trace.arguments:
                        step_trace.arguments = details.get("arguments")
                elif event == "approval_granted":
                    step_trace.approval_granted = True
                elif event == "approval_denied":
                    step_trace.approval_denied = True
                elif event == "step_completed":
                    step_trace.completed = True
                    step_trace.output = details.get("output")
                elif event == "step_failed":
                    step_trace.failed = True
                    step_trace.error = details.get("error")

        return trace


def build_task_trace(logs: list[dict]) -> TaskTrace:
    return TaskTrace.from_logs(logs)
