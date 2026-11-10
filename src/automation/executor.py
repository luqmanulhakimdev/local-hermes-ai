import re
import signal

from src.automation.models import TaskPlan, TaskStatus, StepStatus
from src.automation.registry import ToolRegistry
from src.automation.validator import TaskValidator
from typing import Any, Callable
from src.automation.task_store import TaskStore

STEP_REFERENCE_PATTERN = re.compile(r"^\$step_(\d+)$")

DEFAULT_TOOL_TIMEOUT = 30

MAX_OUTPUT_SIZE = 20_000


class TaskExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        logger=None,
        task_store=None,
        max_output_size: int = MAX_OUTPUT_SIZE,
        tool_timeout: int = DEFAULT_TOOL_TIMEOUT,
        approval_handler: Callable[[TaskPlan, Any, dict], bool] | None = None,
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
        self.approval_handler = approval_handler
        self.task_store = task_store or TaskStore()

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
        self.task_store.save_task(task)

        self._log(
            task.task_id,
            "task_started",
            details={"description": task.description},
        )

        try:
            self.validator.validate(task)
        except Exception as error:
            task.status = TaskStatus.FAILED
            task.steps[0].status = StepStatus.FAILED
            task.steps[0].error = f"{type(error).__name__}: {error}"
            self.task_store.save_task(task)

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

        return self._execute_steps(
            task,
            outputs,
            require_all_pending=True,
        )

    def _execute_steps(
        self,
        task: TaskPlan,
        outputs: dict[int, Any],
        require_all_pending: bool = False,
    ) -> TaskPlan:
        for step in task.steps:
            if step.status == StepStatus.COMPLETED:
                outputs[step.step_id] = step.output
                continue

            if step.status == StepStatus.FAILED:
                task.status = TaskStatus.FAILED
                self.task_store.save_task(task)
                return task

            if step.status == StepStatus.AWAITING_APPROVAL:
                task.status = TaskStatus.AWAITING_APPROVAL
                self.task_store.save_task(task)
                return task

            if require_all_pending and step.status != StepStatus.PENDING:
                task.status = TaskStatus.FAILED

                self._log(
                    task.task_id,
                    "task_failed",
                    step_id=step.step_id,
                    details={
                        "error": "Step is not in pending status",
                    },
                )

                raise ValueError(
                    f"Step {step.step_id} is not in pending status"
                )

            # PENDING atau RUNNING.
            # RUNNING saat resume berarti step sebelumnya
            # kemungkinan terputus/interrupted, sehingga kita ulangi.
            step.status = StepStatus.RUNNING
            step.error = None
            task.status = TaskStatus.RUNNING
            self.task_store.save_task(task)

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

                tool = self.registry.get(step.tool)

                if tool.requires_approval:
                    step.status = StepStatus.AWAITING_APPROVAL
                    task.status = TaskStatus.AWAITING_APPROVAL

                    self.task_store.save_task(task)

                    self._log(
                        task.task_id,
                        "approval_requested",
                        step_id=step.step_id,
                        details={
                            "tool": step.tool,
                            "arguments": arguments,
                        },
                    )

                    if self.approval_handler is None:
                        raise PermissionError(
                            f"Approval required for tool: {step.tool}"
                        )

                    approved = self.approval_handler(
                        task,
                        step,
                        arguments,
                    )

                    if not approved:
                        self._log(
                            task.task_id,
                            "approval_denied",
                            step_id=step.step_id,
                            details={
                                "tool": step.tool,
                            },
                        )

                        step.status = StepStatus.FAILED
                        step.error = (
                            f"Approval denied for tool: {step.tool}"
                        )
                        task.status = TaskStatus.FAILED
                        raise PermissionError(step.error)

                    self._log(
                        task.task_id,
                        "approval_granted",
                        step_id=step.step_id,
                        details={
                            "tool": step.tool,
                        },
                    )

                    step.status = StepStatus.RUNNING
                    task.status = TaskStatus.RUNNING
                    self.task_store.save_task(task)

                result = self._execute_tool(
                    step.tool,
                    arguments,
                )

                self._validate_output_size(result)

                step.output = result
                step.status = StepStatus.COMPLETED
                step.error = None
                outputs[step.step_id] = result

                self.task_store.save_task(task)

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
                self.task_store.save_task(task)

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
                    details={
                        "error": step.error,
                    },
                )

                return task

        task.status = TaskStatus.COMPLETED
        self.task_store.save_task(task)

        self._log(
            task.task_id,
            "task_completed",
            details={
                "steps_completed": len(task.steps),
            },
        )

        return task

    def resume(self, task_id: str) -> TaskPlan:
        task = self.task_store.get_task(task_id)

        if task is None:
            raise ValueError(f"Task not found: {task_id}")

        if task.status == TaskStatus.COMPLETED:
            raise ValueError("Completed tasks cannot be resumed")

        if task.status == TaskStatus.FAILED:
            raise ValueError("Failed tasks cannot be resumed")

        if task.status == TaskStatus.AWAITING_APPROVAL:
            raise ValueError(
                "Tasks awaiting approval cannot be resumed automatically"
            )

        if task.status not in {
            TaskStatus.PENDING,
            TaskStatus.RUNNING,
        }:
            raise ValueError(
                f"Task cannot be resumed from status: {task.status.value}"
            )

        self._log(
            task.task_id,
            "task_resumed",
            details={
                "description": task.description,
            },
        )

        outputs = {}

        for step in task.steps:
            if step.status == StepStatus.COMPLETED:
                outputs[step.step_id] = step.output

        task.status = TaskStatus.RUNNING
        self.task_store.save_task(task)

        return self._execute_steps(
            task,
            outputs,
            require_all_pending=False,
        )

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