
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


MAX_TASK_STEPS = 5


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    step_id: int
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    output: Any = None
    error: str | None = None

    def __post_init__(self):
        if not isinstance(self.step_id, int) or isinstance(self.step_id, bool):
            raise ValueError("step_id must be an integer")

        if self.step_id < 1:
            raise ValueError("step_id must be greater than 0")

        if not isinstance(self.tool, str) or not self.tool.strip():
            raise ValueError("tool must be a non-empty string")

        if not isinstance(self.arguments, dict):
            raise ValueError("arguments must be a dictionary")


@dataclass
class TaskPlan:
    description: str
    steps: list[TaskStep]
    task_id: str = field(default_factory=lambda: str(uuid4()))
    status: TaskStatus = TaskStatus.PENDING

    def __post_init__(self):
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description must not be empty")

        if not isinstance(self.steps, list) or not self.steps:
            raise ValueError("task must contain at least one step")

        if len(self.steps) > MAX_TASK_STEPS:
            raise ValueError(
                f"task cannot contain more than {MAX_TASK_STEPS} steps"
            )

        step_ids = [step.step_id for step in self.steps]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError("step_id values must be unique")

        if step_ids != list(range(1, len(self.steps) + 1)):
            raise ValueError("step_id values must be sequential, starting from 1")


def validate_task_state_consistency(task: TaskPlan) -> None:
    if not isinstance(task, TaskPlan):
        raise TypeError("task must be a TaskPlan")

    if task.status == TaskStatus.COMPLETED:
        for step in task.steps:
            if step.status != StepStatus.COMPLETED:
                raise ValueError(
                    f"Inconsistent state: Task is COMPLETED but step {step.step_id} is {step.status.value}"
                )

    elif task.status == TaskStatus.FAILED:
        has_failed_step = any(step.status == StepStatus.FAILED for step in task.steps)
        if not has_failed_step:
            raise ValueError(
                "Inconsistent state: Task is FAILED but no step is marked FAILED"
            )
        for step in task.steps:
            if step.status == StepStatus.RUNNING:
                raise ValueError(
                    f"Inconsistent state: Task is FAILED but step {step.step_id} is RUNNING"
                )

    elif task.status == TaskStatus.AWAITING_APPROVAL:
        has_awaiting_step = any(
            step.status == StepStatus.AWAITING_APPROVAL for step in task.steps
        )
        if not has_awaiting_step:
            raise ValueError(
                "Inconsistent state: Task is AWAITING_APPROVAL but no step is AWAITING_APPROVAL"
            )
        for step in task.steps:
            if step.status == StepStatus.RUNNING:
                raise ValueError(
                    f"Inconsistent state: Task is AWAITING_APPROVAL but step {step.step_id} is RUNNING"
                )

    elif task.status == TaskStatus.CANCELLED:
        for step in task.steps:
            if step.status == StepStatus.RUNNING:
                raise ValueError(
                    f"Inconsistent state: Task is CANCELLED but step {step.step_id} is RUNNING"
                )

