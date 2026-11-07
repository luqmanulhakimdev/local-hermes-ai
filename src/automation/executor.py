import re
from typing import Any
import signal

from src.automation.models import TaskPlan, TaskStatus, StepStatus
from src.automation.registry import ToolRegistry
from src.automation.validator import TaskValidator

STEP_REFERENCE_PATTERN = re.compile(r"^\$step_(\d+)$")

DEFAULT_TOOL_TIMEOUT = 30

MAX_OUTPUT_SIZE = 20_000


class TaskExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        logger=None,
        max_output_size: int = MAX_OUTPUT_SIZE,
        tool_timeout: int = DEFAULT_TOOL_TIMEOUT,
    ):
        if max_output_size <= 0:
            raise ValueError("max_output_size must be greater than 0")

        if tool_timeout <= 0:
            raise ValueError("tool_timeout must be greater than 0")

        self.registry = registry
        self.logger = logger
        self.validator = TaskValidator(registry)
        self.max_output_size = max_output_size
        self.tool_timeout = tool_timeout

    def _log(self, task_id, event, step_id=None, details=None):
        if self.logger is not None:
            self.logger.log_event(
                task_id=task_id,
                event=event,
                step_id=step_id,
                details=details,
            )

    def _resolve_value(
        self,
        value: Any,
        current_step_id: int,
        outputs: dict[int, Any],
    ) -> Any:
        if isinstance(value, str):
            match = STEP_REFERENCE_PATTERN.fullmatch(value)

            if not match:
                return value

            referenced_step_id = int(match.group(1))

            if referenced_step_id >= current_step_id:
                raise ValueError(
                    "A step can only reference outputs from previous steps"
                )

            if referenced_step_id not in outputs:
                raise ValueError(
                    f"Output for step {referenced_step_id} is unavailable"
                )

            return outputs[referenced_step_id]

        if isinstance(value, list):
            return [
                self._resolve_value(item, current_step_id, outputs)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                key: self._resolve_value(item, current_step_id, outputs)
                for key, item in value.items()
            }

        return value

    def execute(self, task: TaskPlan) -> TaskPlan:
        if task.status != TaskStatus.PENDING:
            raise ValueError("Only pending tasks can be executed")

        task.status = TaskStatus.RUNNING

        self._log(
            task.task_id,
            "task_started",
            details={"description": task.description},
        )

        # Validate the complete plan before executing any tool.
        try:
            self.validator.validate(task)

        except Exception as error:
            task.status = TaskStatus.FAILED
            task.steps[0].status = StepStatus.FAILED
            task.steps[0].error = f"{type(error).__name__}: {error}"

            self._log(
                task.task_id,
                "step_failed",
                step_id=task.steps[0].step_id,
                details={
                    "phase": "validation",
                    "error": task.steps[0].error,
                },
            )

            self._log(
                task.task_id,
                "task_failed",
                step_id=task.steps[0].step_id,
                details={
                    "phase": "validation",
                    "error": task.steps[0].error,
                },
            )

            return task

        outputs = {}

        for step in task.steps:
            if step.status != StepStatus.PENDING:
                task.status = TaskStatus.FAILED

                self._log(
                    task.task_id,
                    "task_failed",
                    step_id=step.step_id,
                    details={"error": "Step is not in pending status"},
                )

                raise ValueError(
                    f"Step {step.step_id} is not in pending status"
                )

            step.status = StepStatus.RUNNING

            try:
                arguments = self._resolve_value(
                    step.arguments,
                    step.step_id,
                    outputs,
                )

                self._log(
                    task.task_id,
                    "step_started",
                    step_id=step.step_id,
                    details={
                        "tool": step.tool,
                        "arguments": arguments,
                    },
                )

                result = self._execute_tool(step.tool, arguments)

                self._validate_output_size(result)

                step.output = result
                step.status = StepStatus.COMPLETED
                outputs[step.step_id] = result

                self._log(
                    task.task_id,
                    "step_completed",
                    step_id=step.step_id,
                    details={
                        "tool": step.tool,
                        "output": result,
                    },
                )

            except Exception as error:
                step.status = StepStatus.FAILED
                step.error = f"{type(error).__name__}: {error}"
                task.status = TaskStatus.FAILED

                self._log(
                    task.task_id,
                    "step_failed",
                    step_id=step.step_id,
                    details={
                        "tool": step.tool,
                        "error": step.error,
                    },
                )

                self._log(
                    task.task_id,
                    "task_failed",
                    step_id=step.step_id,
                    details={"error": step.error},
                )

                break

        else:
            task.status = TaskStatus.COMPLETED

            self._log(
                task.task_id,
                "task_completed",
                details={"steps_completed": len(task.steps)},
            )

        return task

    def _validate_output_size(self, output: Any) -> None:
        if isinstance(output, str):
            output_size = len(output)

            if output_size > self.max_output_size:
                raise ValueError(
                    f"Tool output exceeds maximum allowed size "
                    f"({output_size} > {self.max_output_size} characters)"
                )

    def _handle_timeout(self, signum, frame):
        raise TimeoutError(
            f"Tool execution exceeded {self.tool_timeout} seconds"
        )

    def _execute_tool(self, tool_name: str, arguments: dict) -> Any:
        previous_handler = signal.getsignal(signal.SIGALRM)

        signal.signal(signal.SIGALRM, self._handle_timeout)
        signal.alarm(self.tool_timeout)

        try:
            return self.registry.execute(tool_name, arguments)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)