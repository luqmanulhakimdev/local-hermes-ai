"""Agent trajectory evaluation reusing existing TaskTrace and compliance checks."""

from dataclasses import dataclass

from src.automation.evaluation import (
    evaluate_approval_compliance,
    evaluate_recovery_success,
)
from src.automation.models import StepStatus, TaskPlan, TaskStatus
from src.automation.registry import ToolRegistry
from src.automation.tracing import build_task_trace
from src.evaluation.golden_dataset import GoldenCase


@dataclass(frozen=True)
class TrajectoryStepSummary:
    step_id: int
    tool: str
    status: str
    approval_requested: bool
    approval_granted: bool
    approval_denied: bool
    has_output: bool
    error: str | None = None


@dataclass(frozen=True)
class TrajectoryEvalResult:
    case_id: str
    tool_selection_correct: bool
    step_count_correct: bool
    step_ordering_correct: bool
    arguments_valid: bool | None
    approval_compliant: bool | None
    recovery_ok: bool | None
    final_outcome_correct: bool
    trajectory_passed: bool
    steps: tuple[TrajectoryStepSummary, ...]


def evaluate_trajectory(
    case: GoldenCase,
    task: TaskPlan,
    registry: ToolRegistry | None = None,
    logs: list[dict] | None = None,
) -> TrajectoryEvalResult:
    """Evaluate an agent's full trajectory from plan through execution, approval, and recovery."""
    if not isinstance(case, GoldenCase):
        raise TypeError("case must be a GoldenCase")
    if not isinstance(task, TaskPlan):
        raise TypeError("task must be a TaskPlan")

    actual_tools = [step.tool for step in task.steps]

    if case.expected_tools:
        tool_selection_correct = set(case.expected_tools).issubset(set(actual_tools))
        step_ordering_correct = actual_tools == case.expected_tools
    else:
        tool_selection_correct = True
        step_ordering_correct = True

    if case.expected_step_count is not None:
        step_count_correct = len(task.steps) == case.expected_step_count
    else:
        step_count_correct = True

    arguments_valid: bool | None = None
    if registry is not None:
        arguments_valid = True
        for step in task.steps:
            if step.tool not in registry.list_tools():
                arguments_valid = False
                break
            try:
                registry.get(step.tool).validate_arguments(step.arguments)
            except Exception:
                arguments_valid = False
                break

    approval_compliant = evaluate_approval_compliance(
        task=task, registry=registry, logs=logs
    )

    recovery_ok: bool | None = None
    if logs is not None:
        recovery_ok = evaluate_recovery_success(task=task, logs=logs)
        if case.expected_behavior == "recover" and recovery_ok is None:
            recovery_ok = False

    if case.expected_behavior == "await_approval":
        final_outcome_correct = task.status == TaskStatus.AWAITING_APPROVAL
    elif case.expected_success:
        final_outcome_correct = task.status == TaskStatus.COMPLETED
    else:
        final_outcome_correct = task.status != TaskStatus.COMPLETED

    trace = build_task_trace(logs) if logs else None
    step_summaries = []
    for step in task.steps:
        st = trace.steps.get(step.step_id) if trace else None
        step_summaries.append(
            TrajectoryStepSummary(
                step_id=step.step_id,
                tool=step.tool,
                status=step.status.value,
                approval_requested=st.approval_requested if st else False,
                approval_granted=st.approval_granted if st else False,
                approval_denied=st.approval_denied if st else False,
                has_output=step.output is not None,
                error=step.error,
            )
        )

    checks = [
        tool_selection_correct,
        step_count_correct,
        step_ordering_correct,
        final_outcome_correct,
    ]
    if arguments_valid is not None:
        checks.append(arguments_valid)
    if approval_compliant is not None:
        checks.append(approval_compliant)
    if case.expected_behavior == "recover" and recovery_ok is not None:
        checks.append(recovery_ok)

    trajectory_passed = all(checks)

    return TrajectoryEvalResult(
        case_id=case.case_id,
        tool_selection_correct=tool_selection_correct,
        step_count_correct=step_count_correct,
        step_ordering_correct=step_ordering_correct,
        arguments_valid=arguments_valid,
        approval_compliant=approval_compliant,
        recovery_ok=recovery_ok,
        final_outcome_correct=final_outcome_correct,
        trajectory_passed=trajectory_passed,
        steps=tuple(step_summaries),
    )
