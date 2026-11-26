"""Structured failure analysis and clustering distinguishing observed facts vs inference."""

from collections import Counter
from dataclasses import dataclass

from src.evaluation.golden_dataset import GoldenCase
from src.evaluation.llm_eval import LLMEvalResult
from src.evaluation.rag_eval import RAGEvalResult
from src.evaluation.trajectory_eval import TrajectoryEvalResult

FAILURE_CATEGORIES = {
    "planning_error",
    "tool_selection_error",
    "argument_error",
    "retrieval_error",
    "grounding_error",
    "hallucination",
    "execution_error",
    "approval_error",
    "safety_violation",
    "recovery_error",
    "timeout",
    "resource_limit",
    "unknown",
}

CATEGORY_TO_SUBSYSTEM = {
    "planning_error": "planner",
    "tool_selection_error": "planner",
    "argument_error": "validator",
    "retrieval_error": "rag_retriever",
    "grounding_error": "rag_qa",
    "hallucination": "llm_generation",
    "execution_error": "executor",
    "approval_error": "approval_gate",
    "safety_violation": "security_boundary",
    "recovery_error": "task_store_resume",
    "timeout": "executor_limits",
    "resource_limit": "executor_limits",
    "unknown": "unknown",
}


@dataclass(frozen=True)
class FailureReport:
    case_id: str
    request: str
    expected: str
    actual: str
    failure_category: str
    severity: str
    observed_facts: tuple[str, ...]
    inferred_root_cause: str
    confidence: str
    suggested_area: str
    trace_summary: str | None = None

    def __post_init__(self):
        if self.failure_category not in FAILURE_CATEGORIES:
            raise ValueError(f"Invalid failure_category: {self.failure_category}")
        if self.severity not in {"critical", "high", "medium", "low"}:
            raise ValueError(f"Invalid severity: {self.severity}")
        if self.confidence not in {"high", "medium", "low"}:
            raise ValueError(f"Invalid confidence: {self.confidence}")


@dataclass(frozen=True)
class FailureClusterSummary:
    total_failures: int
    counts_by_category: dict[str, int]
    most_frequent_category: str | None
    affected_cases_by_category: dict[str, tuple[str, ...]]
    affected_subsystems: tuple[str, ...]


def analyze_failure(
    case: GoldenCase,
    actual_summary: str,
    error_message: str | None = None,
    trajectory_result: TrajectoryEvalResult | None = None,
    rag_result: RAGEvalResult | None = None,
    llm_result: LLMEvalResult | None = None,
) -> FailureReport:
    """Classify a failure deterministically, separating observed facts from inferred cause."""
    facts: list[str] = []
    category = "unknown"
    severity = "medium"
    confidence = "low"
    inferred = "Insufficient evidence to isolate root cause."

    if error_message:
        facts.append(f"Observed error: {error_message}")
    if actual_summary:
        facts.append(f"Observed outcome: {actual_summary}")

    err_lower = (error_message or "").lower()

    if case.category == "security":
        category = "safety_violation"
        severity = "critical"
        confidence = "high"
        inferred = "Security boundary did not reject or contain hostile input as expected."
    elif "timeout" in err_lower or "timed out" in err_lower:
        category = "timeout"
        severity = "high"
        confidence = "high"
        inferred = "Execution exceeded configured timeout threshold."
    elif "maximum allowed size" in err_lower or "exceeds maximum" in err_lower:
        category = "resource_limit"
        severity = "medium"
        confidence = "high"
        inferred = "Input or output exceeded configured resource budget."
    elif "approval" in err_lower or (
        trajectory_result is not None and trajectory_result.approval_compliant is False
    ):
        category = "approval_error"
        severity = "critical"
        confidence = "high"
        facts.append("Approval compliance check returned False.")
        inferred = "Sensitive tool lacked valid human approval flow."
    elif rag_result is not None and not rag_result.passed:
        if rag_result.failure_stage == "retrieval_failure":
            category = "retrieval_error"
            severity = "high"
            confidence = "high"
            facts.append("Expected sources were not present in retrieved chunks.")
            inferred = "Vector retrieval missed relevant document or threshold filtered it out."
        elif rag_result.failure_stage == "grounding_failure":
            category = "grounding_error"
            severity = "high"
            confidence = "medium"
            facts.append("Relevant sources were retrieved, but answer lacked grounding.")
            inferred = "Generator ignored retrieved context or omitted required facts."
        elif rag_result.failure_stage == "abstention_failure":
            category = "hallucination"
            severity = "high"
            confidence = "medium"
            facts.append("Model answered instead of abstaining on unanswerable query.")
            inferred = "Prompt failed to enforce abstention when evidence was missing."
    elif trajectory_result is not None and not trajectory_result.trajectory_passed:
        if not trajectory_result.tool_selection_correct:
            category = "tool_selection_error"
            severity = "high"
            confidence = "high"
            facts.append("Selected tools did not match expected tools.")
            inferred = "Planner selected an unexpected or incorrect tool."
        elif not trajectory_result.step_count_correct or not trajectory_result.step_ordering_correct:
            category = "planning_error"
            severity = "high"
            confidence = "high"
            facts.append("Plan step count or ordering differed from expected trajectory.")
            inferred = "Planner generated an invalid or suboptimal step sequence."
        elif trajectory_result.arguments_valid is False:
            category = "argument_error"
            severity = "high"
            confidence = "high"
            facts.append("Tool argument validation failed.")
            inferred = "Planner supplied missing or unexpected tool arguments."
        elif case.expected_behavior == "recover" and trajectory_result.recovery_ok is False:
            category = "recovery_error"
            severity = "high"
            confidence = "high"
            facts.append("Recovery trajectory check failed.")
            inferred = "Interrupted task failed to resume cleanly from persisted state."
        else:
            category = "execution_error"
            severity = "high"
            confidence = "medium"
            inferred = "Step execution failed before reaching expected final status."
    elif llm_result is not None and not llm_result.passed:
        if llm_result.abstention_ok is False:
            category = "hallucination"
            severity = "high"
            confidence = "medium"
            facts.append("Abstention check failed.")
            inferred = "Model fabricated an answer when it should have abstained."
        elif llm_result.instruction_following is False:
            category = "planning_error"
            severity = "medium"
            confidence = "medium"
            facts.append("Structured output format check failed.")
            inferred = "Model did not adhere to requested output schema."

    trace_summary = None
    if trajectory_result and trajectory_result.steps:
        trace_summary = " -> ".join(
            f"{s.step_id}:{s.tool}({s.status})" for s in trajectory_result.steps
        )

    expected_desc = (
        case.expected_output
        or case.expected_behavior
        or (", ".join(case.expected_tools) if case.expected_tools else "success")
    )

    return FailureReport(
        case_id=case.case_id,
        request=case.input_text,
        expected=expected_desc,
        actual=actual_summary,
        failure_category=category,
        severity=severity,
        observed_facts=tuple(facts),
        inferred_root_cause=inferred,
        confidence=confidence,
        suggested_area=CATEGORY_TO_SUBSYSTEM.get(category, "unknown"),
        trace_summary=trace_summary,
    )


def cluster_failures(reports: list[FailureReport]) -> FailureClusterSummary:
    """Aggregate failure reports by category and affected subsystem."""
    if not reports:
        return FailureClusterSummary(
            total_failures=0,
            counts_by_category={},
            most_frequent_category=None,
            affected_cases_by_category={},
            affected_subsystems=(),
        )

    counts = Counter(r.failure_category for r in reports)
    affected: dict[str, list[str]] = {}
    subsystems: set[str] = set()

    for r in reports:
        affected.setdefault(r.failure_category, []).append(r.case_id)
        subsystems.add(r.suggested_area)

    most_freq = counts.most_common(1)[0][0]

    return FailureClusterSummary(
        total_failures=len(reports),
        counts_by_category=dict(sorted(counts.items())),
        most_frequent_category=most_freq,
        affected_cases_by_category={
            k: tuple(v) for k, v in sorted(affected.items())
        },
        affected_subsystems=tuple(sorted(subsystems)),
    )
