import re

from src.automation.models import TaskPlan
from src.automation.registry import ToolRegistry

STEP_REFERENCE_PATTERN = re.compile(r"^\$step_(\d+)$")


class TaskValidator:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def _validate_references(self, value, current_step_id, available_step_ids):
        if isinstance(value, str):
            match = STEP_REFERENCE_PATTERN.fullmatch(value)

            if match:
                referenced_id = int(match.group(1))

                if referenced_id not in available_step_ids:
                    raise ValueError(
                        f"Referenced step does not exist: $step_{referenced_id}"
                    )

                if referenced_id >= current_step_id:
                    raise ValueError(
                        f"Step {current_step_id} can only reference previous steps"
                    )

        elif isinstance(value, list):
            for item in value:
                self._validate_references(
                    item,
                    current_step_id,
                    available_step_ids,
                )

        elif isinstance(value, dict):
            for item in value.values():
                self._validate_references(
                    item,
                    current_step_id,
                    available_step_ids,
                )

    def validate(self, task: TaskPlan):
        if not isinstance(task, TaskPlan):
            raise TypeError("Expected a TaskPlan")

        if not task.steps:
            raise ValueError("Task must contain at least one step")

        if len(task.steps) > 5:
            raise ValueError("Task cannot contain more than 5 steps")

        expected_step_ids = list(range(1, len(task.steps) + 1))
        actual_step_ids = [step.step_id for step in task.steps]

        if actual_step_ids != expected_step_ids:
            raise ValueError(
                "Step IDs must be sequential starting from 1"
            )

        available_step_ids = set(actual_step_ids)

        for step in task.steps:
            # Ensure tool exists and is allowed.
            tool = self.registry.get(step.tool)

            # Validate required arguments.
            tool.validate_arguments(step.arguments)

            # Validate references to previous steps.
            self._validate_references(
                step.arguments,
                step.step_id,
                available_step_ids,
            )

        return True