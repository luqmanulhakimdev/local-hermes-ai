from dataclasses import dataclass

from src.automation.models import TaskPlan, TaskStatus, StepStatus
from src.automation.registry import ToolRegistry
from src.automation.tracing import StepTrace, TaskTrace, build_task_trace
from src.automation.evaluation_cases import EVALUATION_CASES, REFERENCE_PLANS


@dataclass(frozen=True)
class EvaluationMetrics:
    plan_valid: bool
    task_success: bool
    step_success_rate: float
    approval_compliance: bool | None
    recovery_success: bool | None
    trace_complete: bool | None

    def __post_init__(self):
        if not isinstance(self.plan_valid, bool):
            raise ValueError("plan_valid must be a boolean")

        if not isinstance(self.task_success, bool):
            raise ValueError("task_success must be a boolean")

        if not isinstance(self.step_success_rate, (int, float)):
            raise ValueError("step_success_rate must be numeric")

        if not 0.0 <= self.step_success_rate <= 1.0:
            raise ValueError(
                "step_success_rate must be between 0.0 and 1.0"
            )

        if self.approval_compliance is not None:
            if not isinstance(self.approval_compliance, bool):
                raise ValueError(
                    "approval_compliance must be a boolean or None"
                )

        if self.recovery_success is not None:
            if not isinstance(self.recovery_success, bool):
                raise ValueError(
                    "recovery_success must be a boolean or None"
                )

        if self.trace_complete is not None:
            if not isinstance(self.trace_complete, bool):
                raise ValueError(
                    "trace_complete must be a boolean or None"
                )

    @classmethod
    def from_task(
        cls,
        task: TaskPlan,
        plan_valid: bool,
        logs: list[dict] | None = None,
        registry: ToolRegistry | None = None,
    ) -> "EvaluationMetrics":
        if not isinstance(task, TaskPlan):
            raise TypeError("task must be a TaskPlan")

        if not isinstance(plan_valid, bool):
            raise ValueError("plan_valid must be a boolean")

        completed_steps = sum(
            step.status == StepStatus.COMPLETED
            for step in task.steps
        )

        step_success_rate = completed_steps / len(task.steps)

        recovery_success = None
        trace_complete = None
        approval_compliance = None

        if logs is not None:
            recovery_success = evaluate_recovery_success(task=task, logs=logs)
            trace_complete = evaluate_trace_completeness(logs=logs, task=task)
            approval_compliance = evaluate_approval_compliance(
                task=task, registry=registry, logs=logs
            )
        elif registry is not None:
            approval_compliance = evaluate_approval_compliance(
                task=task, registry=registry, logs=None
            )

        return cls(
            plan_valid=plan_valid,
            task_success=task.status == TaskStatus.COMPLETED,
            step_success_rate=step_success_rate,
            approval_compliance=approval_compliance,
            recovery_success=recovery_success,
            trace_complete=trace_complete,
        )

@dataclass(frozen=True)
class PlanningEvaluation:
    tool_sequence_correct: bool
    step_count_correct: bool
    planning_success: bool

    def __post_init__(self):
        if not isinstance(self.tool_sequence_correct, bool):
            raise ValueError(
                "tool_sequence_correct must be a boolean"
            )

        if not isinstance(self.step_count_correct, bool):
            raise ValueError(
                "step_count_correct must be a boolean"
            )

        if not isinstance(self.planning_success, bool):
            raise ValueError(
                "planning_success must be a boolean"
            )


def evaluate_planning(case, plan) -> PlanningEvaluation:
    from src.automation.evaluation_dataset import EvaluationCase

    if not isinstance(case, EvaluationCase):
        raise TypeError("case must be an EvaluationCase")

    if not isinstance(plan, TaskPlan):
        raise TypeError("plan must be a TaskPlan")

    actual_tools = [step.tool for step in plan.steps]

    tool_sequence_correct = (
        actual_tools[:len(case.expected_tools)]
        == case.expected_tools
    )

    step_count_correct = (
        len(plan.steps) == case.expected_step_count
    )

    planning_success = (
        tool_sequence_correct
        and step_count_correct
    )

    return PlanningEvaluation(
        tool_sequence_correct=tool_sequence_correct,
        step_count_correct=step_count_correct,
        planning_success=planning_success,
    )

def evaluate_planning_dataset(cases, plans):
    if not isinstance(cases, list):
        raise TypeError("cases must be a list")

    if not isinstance(plans, dict):
        raise TypeError("plans must be a dictionary")

    results = []

    for case in cases:
        if case.case_id not in plans:
            raise ValueError(
                f"Missing plan for evaluation case: {case.case_id}"
            )

        result = evaluate_planning(
            case,
            plans[case.case_id],
        )

        results.append(result)

    return results

def evaluate_tool_selection(case, plan) -> bool:
    from src.automation.evaluation_dataset import EvaluationCase

    if not isinstance(case, EvaluationCase):
        raise TypeError("case must be an EvaluationCase")

    if not isinstance(plan, TaskPlan):
        raise TypeError("plan must be a TaskPlan")

    actual_tools = [step.tool for step in plan.steps]

    return actual_tools == case.expected_tools

def evaluate_tool_selection_dataset(cases, plans) -> float:
    from src.automation.evaluation_dataset import EvaluationCase

    if not isinstance(cases, list):
        raise TypeError("cases must be a list")

    if not isinstance(plans, dict):
        raise TypeError("plans must be a dictionary")

    if not cases:
        raise ValueError("cases must not be empty")

    correct = 0

    for case in cases:
        if not isinstance(case, EvaluationCase):
            raise TypeError("cases must contain EvaluationCase objects")

        if case.case_id not in plans:
            raise ValueError(
                f"Missing plan for evaluation case: {case.case_id}"
            )

        if evaluate_tool_selection(case, plans[case.case_id]):
            correct += 1

    return correct / len(cases)


@dataclass(frozen=True)
class ExecutionEvaluation:
    execution_success: bool
    expected_success: bool
    outcome_match: bool

    def __post_init__(self):
        if not isinstance(self.execution_success, bool):
            raise ValueError("execution_success must be a boolean")

        if not isinstance(self.expected_success, bool):
            raise ValueError("expected_success must be a boolean")

        if not isinstance(self.outcome_match, bool):
            raise ValueError("outcome_match must be a boolean")


def evaluate_execution_outcome(case, task: TaskPlan) -> ExecutionEvaluation:
    from src.automation.evaluation_dataset import EvaluationCase

    if not isinstance(case, EvaluationCase):
        raise TypeError("case must be an EvaluationCase")

    if not isinstance(task, TaskPlan):
        raise TypeError("task must be a TaskPlan")

    execution_success = (task.status == TaskStatus.COMPLETED)
    expected_success = case.expected_success
    outcome_match = (execution_success == expected_success)

    return ExecutionEvaluation(
        execution_success=execution_success,
        expected_success=expected_success,
        outcome_match=outcome_match,
    )


def evaluate_execution_dataset(cases: list, tasks: dict[str, TaskPlan]) -> list[ExecutionEvaluation]:
    from src.automation.evaluation_dataset import EvaluationCase

    if not isinstance(cases, list):
        raise TypeError("cases must be a list")

    if not isinstance(tasks, dict):
        raise TypeError("tasks must be a dictionary")

    results = []

    for case in cases:
        if not isinstance(case, EvaluationCase):
            raise TypeError("cases must contain EvaluationCase objects")

        if case.case_id not in tasks:
            raise ValueError(
                f"Missing task for evaluation case: {case.case_id}"
            )

        result = evaluate_execution_outcome(
            case,
            tasks[case.case_id],
        )
        results.append(result)

    return results


def evaluate_execution_outcome_dataset(cases: list, tasks: dict[str, TaskPlan]) -> float:
    if not isinstance(cases, list):
        raise TypeError("cases must be a list")

    if not cases:
        raise ValueError("cases must not be empty")

    results = evaluate_execution_dataset(cases, tasks)
    correct = sum(1 for res in results if res.outcome_match)
    return correct / len(cases)


@dataclass(frozen=True)
class EvaluationSummary:
    total_cases: int
    planning_accuracy: float
    tool_selection_accuracy: float
    execution_outcome_accuracy: float

    def __post_init__(self):
        if (
            not isinstance(self.total_cases, int)
            or isinstance(self.total_cases, bool)
            or self.total_cases <= 0
        ):
            raise ValueError("total_cases must be a positive integer")

        for attr in (
            "planning_accuracy",
            "tool_selection_accuracy",
            "execution_outcome_accuracy",
        ):
            val = getattr(self, attr)
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise ValueError(f"{attr} must be a float")
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{attr} must be between 0.0 and 1.0")


def calculate_evaluation_summary(
    cases: list,
    plans: dict[str, TaskPlan],
    executed_tasks: dict[str, TaskPlan] | None = None,
) -> EvaluationSummary:
    from src.automation.evaluation_dataset import EvaluationCase

    if not isinstance(cases, list):
        raise TypeError("cases must be a list")

    if not isinstance(plans, dict):
        raise TypeError("plans must be a dictionary")

    if not cases:
        raise ValueError("cases must not be empty")

    for case in cases:
        if not isinstance(case, EvaluationCase):
            raise TypeError("cases must contain EvaluationCase objects")
        if case.case_id not in plans:
            raise ValueError(
                f"Missing plan for evaluation case: {case.case_id}"
            )

    tasks_to_evaluate = executed_tasks if executed_tasks is not None else plans

    if not isinstance(tasks_to_evaluate, dict):
        raise TypeError("executed_tasks must be a dictionary")

    for case in cases:
        if case.case_id not in tasks_to_evaluate:
            raise ValueError(
                f"Missing executed task for evaluation case: {case.case_id}"
            )

    planning_results = evaluate_planning_dataset(cases, plans)
    planning_accuracy = sum(
        1 for res in planning_results if res.planning_success
    ) / len(cases)

    tool_selection_accuracy = evaluate_tool_selection_dataset(cases, plans)

    execution_outcome_accuracy = evaluate_execution_outcome_dataset(
        cases,
        tasks_to_evaluate,
    )

    return EvaluationSummary(
        total_cases=len(cases),
        planning_accuracy=planning_accuracy,
        tool_selection_accuracy=tool_selection_accuracy,
        execution_outcome_accuracy=execution_outcome_accuracy,
    )


@dataclass(frozen=True)
class RunMetrics:
    run_id: str
    task_id: str
    task_status: TaskStatus
    step_count: int
    completed_steps: int
    failed_steps: int
    approval_requests: int
    approval_denials: int
    duration_seconds: float | None = None

    def __post_init__(self):
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise ValueError("run_id must be a non-empty string")

        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string")

        if not isinstance(self.task_status, TaskStatus):
            raise ValueError("task_status must be a TaskStatus")

        for attr in (
            "step_count",
            "completed_steps",
            "failed_steps",
            "approval_requests",
            "approval_denials",
        ):
            val = getattr(self, attr)
            if not isinstance(val, int) or isinstance(val, bool) or val < 0:
                raise ValueError(f"{attr} must be a non-negative integer")

        if self.duration_seconds is not None:
            if (
                not isinstance(self.duration_seconds, (int, float))
                or isinstance(self.duration_seconds, bool)
            ):
                raise ValueError("duration_seconds must be numeric or None")
            if self.duration_seconds < 0.0:
                raise ValueError("duration_seconds must be non-negative")


def collect_run_metrics(
    task: TaskPlan,
    logs: list[dict] | None = None,
    run_id: str | None = None,
) -> RunMetrics:
    from datetime import datetime

    if not isinstance(task, TaskPlan):
        raise TypeError("task must be a TaskPlan")

    effective_run_id = run_id or task.task_id
    completed_steps = sum(
        1 for step in task.steps if step.status == StepStatus.COMPLETED
    )
    failed_steps = sum(
        1 for step in task.steps if step.status == StepStatus.FAILED
    )

    approval_requests = 0
    approval_denials = 0
    duration_seconds = None

    if logs is not None:
        if not isinstance(logs, list):
            raise TypeError("logs must be a list or None")

        approval_requests = sum(
            1 for log in logs if isinstance(log, dict) and log.get("event") == "approval_requested"
        )
        approval_denials = sum(
            1 for log in logs if isinstance(log, dict) and log.get("event") == "approval_denied"
        )

        timestamps = []
        for log in logs:
            if isinstance(log, dict) and "created_at" in log:
                try:
                    timestamps.append(datetime.fromisoformat(log["created_at"]))
                except (ValueError, TypeError):
                    pass

        if len(timestamps) >= 2:
            duration_seconds = max(0.0, (timestamps[-1] - timestamps[0]).total_seconds())

    return RunMetrics(
        run_id=effective_run_id,
        task_id=task.task_id,
        task_status=task.status,
        step_count=len(task.steps),
        completed_steps=completed_steps,
        failed_steps=failed_steps,
        approval_requests=approval_requests,
        approval_denials=approval_denials,
        duration_seconds=duration_seconds,
    )


def evaluate_recovery_success(
    task: TaskPlan | None = None,
    logs: list[dict] | None = None,
) -> bool | None:
    if task is not None and not isinstance(task, TaskPlan):
        raise TypeError("task must be a TaskPlan")
    if logs is not None and not isinstance(logs, list):
        raise TypeError("logs must be a list of log dicts")

    if not logs:
        return None

    resumed_indices = [
        i for i, log in enumerate(logs)
        if isinstance(log, dict) and log.get("event") == "task_resumed"
    ]
    if not resumed_indices:
        return None

    last_resume_idx = resumed_indices[-1]

    if task is not None:
        return task.status == TaskStatus.COMPLETED

    subsequent_logs = logs[last_resume_idx + 1:]
    for log in reversed(subsequent_logs):
        if isinstance(log, dict):
            if log.get("event") == "task_completed":
                return True
            if log.get("event") == "task_failed":
                return False

    return False


def evaluate_trace_completeness(
    logs: list[dict],
    task: TaskPlan | None = None,
) -> bool:
    if not isinstance(logs, list):
        raise TypeError("logs must be a list of log dicts")
    if not all(isinstance(log, dict) for log in logs):
        raise TypeError("logs must contain only dictionary objects")
    if task is not None and not isinstance(task, TaskPlan):
        raise TypeError("task must be a TaskPlan")

    if not logs:
        return False

    events = [log.get("event") for log in logs]

    if "task_started" not in events:
        return False

    has_completed = "task_completed" in events
    has_failed = "task_failed" in events
    if not (has_completed or has_failed):
        return False

    step_events: dict[int, list[str]] = {}
    for log in logs:
        event = log.get("event")
        step_id = log.get("step_id")
        if step_id is not None:
            if step_id not in step_events:
                step_events[step_id] = []
            step_events[step_id].append(event)

    if task is not None:
        if has_completed:
            for step in task.steps:
                evs = step_events.get(step.step_id, [])
                if "step_started" not in evs or "step_completed" not in evs:
                    return False
        elif has_failed:
            has_failed_step = any(
                "step_failed" in evs or "approval_denied" in evs
                for evs in step_events.values()
            )
            if not has_failed_step and not has_failed:
                return False
    else:
        if not step_events:
            return False
        for s_id, evs in step_events.items():
            if "step_started" not in evs:
                return False
            if not ("step_completed" in evs or "step_failed" in evs):
                return False

    for log in logs:
        if log.get("event") == "approval_requested":
            step_id = log.get("step_id")
            evs = step_events.get(step_id, [])
            if not ("approval_granted" in evs or "approval_denied" in evs):
                return False

    return True


def evaluate_approval_compliance(
    task: TaskPlan,
    registry: ToolRegistry | None = None,
    logs: list[dict] | None = None,
) -> bool | None:
    if not isinstance(task, TaskPlan):
        raise TypeError("task must be a TaskPlan")
    if registry is not None and not isinstance(registry, ToolRegistry):
        raise TypeError("registry must be a ToolRegistry")
    if logs is not None and not isinstance(logs, list):
        raise TypeError("logs must be a list of log dicts")

    steps_requiring_approval = []
    if registry is not None:
        for step in task.steps:
            if step.tool in registry.list_tools():
                tool_def = registry.get(step.tool)
                if tool_def.requires_approval:
                    steps_requiring_approval.append(step)
    else:
        if logs is not None:
            for log in logs:
                if isinstance(log, dict) and log.get("event") == "approval_requested":
                    step_id = log.get("step_id")
                    steps_requiring_approval.extend(
                        [s for s in task.steps if s.step_id == step_id]
                    )

    if not steps_requiring_approval:
        return True

    if logs is None:
        return None

    log_events_by_step: dict[int, list[dict]] = {}
    for log in logs:
        if isinstance(log, dict):
            s_id = log.get("step_id")
            if s_id is not None:
                log_events_by_step.setdefault(s_id, []).append(log)

    for step in steps_requiring_approval:
        step_logs = log_events_by_step.get(step.step_id, [])
        events = [l.get("event") for l in step_logs]

        if "approval_denied" in events:
            return False

        if "approval_requested" not in events or "approval_granted" not in events:
            return False

    return True


class RegressionEvaluator:
    def __init__(
        self,
        cases: list[EvaluationCase] | None = None,
        reference_plans: dict[str, TaskPlan] | None = None,
    ):
        self.cases = cases if cases is not None else EVALUATION_CASES
        self.reference_plans = (
            reference_plans if reference_plans is not None else REFERENCE_PLANS
        )

        if not isinstance(self.cases, list):
            raise TypeError("cases must be a list of EvaluationCase")
        if not isinstance(self.reference_plans, dict):
            raise TypeError("reference_plans must be a dictionary")

    def evaluate(self, strict: bool = False) -> EvaluationSummary:
        summary = calculate_evaluation_summary(
            cases=self.cases,
            plans=self.reference_plans,
            executed_tasks=self.reference_plans,
        )

        if strict:
            if (
                summary.planning_accuracy < 1.0
                or summary.tool_selection_accuracy < 1.0
                or summary.execution_outcome_accuracy < 1.0
            ):
                raise RuntimeError(
                    f"Regression evaluation failed in strict mode: {summary}"
                )

        return summary

    def summary_text(self, summary: EvaluationSummary | None = None) -> str:
        if summary is None:
            summary = self.evaluate(strict=False)
        return (
            "Evaluation Summary\n"
            "------------------\n"
            f"Total cases: {summary.total_cases}\n"
            f"Planning accuracy: {summary.planning_accuracy:.2f}\n"
            f"Tool selection accuracy: {summary.tool_selection_accuracy:.2f}\n"
            f"Execution outcome accuracy: {summary.execution_outcome_accuracy:.2f}"
        )


def run_regression_evaluation(
    cases: list[EvaluationCase] | None = None,
    reference_plans: dict[str, TaskPlan] | None = None,
    strict: bool = False,
) -> tuple[EvaluationSummary, str]:
    evaluator = RegressionEvaluator(cases=cases, reference_plans=reference_plans)
    summary = evaluator.evaluate(strict=strict)
    text = evaluator.summary_text(summary)
    return summary, text


def generate_evaluation_report(
    summary: EvaluationSummary,
    recovery_success: bool | float | None = None,
    trace_completeness: bool | float | None = None,
    approval_compliance: bool | float | None = None,
    failures: list[str] | None = None,
) -> str:
    if not isinstance(summary, EvaluationSummary):
        raise TypeError("summary must be an EvaluationSummary")

    def _fmt(val: bool | float | None) -> str:
        if val is None:
            return "N/A"
        if isinstance(val, bool):
            return "True" if val else "False"
        if isinstance(val, (int, float)):
            return f"{val:.2f}"
        return str(val)

    if not failures:
        failures_section = "None"
    else:
        failures_section = "\n".join(
            f if f.startswith("- ") else f"- {f}" for f in failures
        )

    return (
        "Stage 13 Evaluation Report\n"
        "==========================\n\n"
        "Dataset\n"
        "-------\n"
        f"Total cases: {summary.total_cases}\n\n"
        "Planning\n"
        "--------\n"
        f"Planning accuracy: {summary.planning_accuracy:.2f}\n"
        f"Tool selection accuracy: {summary.tool_selection_accuracy:.2f}\n\n"
        "Execution\n"
        "---------\n"
        f"Execution outcome accuracy: {summary.execution_outcome_accuracy:.2f}\n\n"
        "Reliability\n"
        "-----------\n"
        f"Recovery success: {_fmt(recovery_success)}\n"
        f"Trace completeness: {_fmt(trace_completeness)}\n"
        f"Approval compliance: {_fmt(approval_compliance)}\n\n"
        "Failures\n"
        "--------\n"
        f"{failures_section}"
    )


@dataclass(frozen=True)
class RAGEvaluationMetrics:
    case_id: str
    plan_valid: bool
    expected_tools_matched: bool
    context_used: bool
    safety_preserved: bool
    step_count_matched: bool

    def __post_init__(self):
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        if not isinstance(self.plan_valid, bool):
            raise ValueError("plan_valid must be a boolean")
        if not isinstance(self.expected_tools_matched, bool):
            raise ValueError("expected_tools_matched must be a boolean")
        if not isinstance(self.context_used, bool):
            raise ValueError("context_used must be a boolean")
        if not isinstance(self.safety_preserved, bool):
            raise ValueError("safety_preserved must be a boolean")
        if not isinstance(self.step_count_matched, bool):
            raise ValueError("step_count_matched must be a boolean")


def evaluate_rag_case(
    case,
    plan: TaskPlan,
    context=None,
    registry: ToolRegistry | None = None,
) -> RAGEvaluationMetrics:
    from src.automation.evaluation_dataset import EvaluationCase
    from src.automation.validator import TaskValidator

    if not isinstance(case, EvaluationCase):
        raise TypeError("case must be an EvaluationCase")
    if not isinstance(plan, TaskPlan):
        raise TypeError("plan must be a TaskPlan")

    plan_valid = True
    safety_preserved = True
    if registry is not None:
        validator = TaskValidator(registry=registry)
        try:
            validator.validate(plan)
        except Exception:
            plan_valid = False
            safety_preserved = False

    actual_tools = [step.tool for step in plan.steps]
    expected_tools_matched = actual_tools == case.expected_tools
    step_count_matched = len(plan.steps) == case.expected_step_count
    context_used = context is not None and getattr(context, "has_content", False)

    return RAGEvaluationMetrics(
        case_id=case.case_id,
        plan_valid=plan_valid,
        expected_tools_matched=expected_tools_matched,
        context_used=context_used,
        safety_preserved=safety_preserved,
        step_count_matched=step_count_matched,
    )




