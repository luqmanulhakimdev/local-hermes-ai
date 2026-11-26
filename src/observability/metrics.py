"""Deterministic latency, error, token, and cost metrics."""

from collections import Counter
from dataclasses import dataclass
from typing import Any

from src.observability.tracing import RunTrace

ERROR_CATEGORIES = {
    "validation_error",
    "planning_error",
    "tool_error",
    "execution_error",
    "retrieval_error",
    "llm_error",
    "approval_error",
    "timeout_error",
    "resource_limit_error",
    "persistence_error",
    "recovery_error",
    "unknown_error",
}


@dataclass(frozen=True)
class LatencyBreakdown:
    total_ms: float | None
    planning_ms: float | None
    retrieval_ms: float | None
    llm_ms: float | None
    tools_ms: float | None
    approval_ms: float | None
    other_ms: float | None
    attribution_mode: str  # "measured", "partial", "unknown"


@dataclass(frozen=True)
class ErrorMetrics:
    total_errors: int
    failed_runs: int
    failed_tasks: int
    failed_steps: int
    failed_tools: int
    approval_denials: int
    retrieval_failures: int
    llm_failures: int
    timeouts: int
    resource_limit_failures: int
    validation_failures: int
    counts_by_category: dict[str, int]
    step_error_rate: float | None
    tool_error_rate: float | None
    task_error_rate: float | None
    run_error_rate: float | None


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    llm_calls: int


@dataclass(frozen=True)
class PricingConfig:
    input_cost_per_1k_tokens: float
    output_cost_per_1k_tokens: float
    currency: str = "USD"

    def __post_init__(self):
        for attr in ("input_cost_per_1k_tokens", "output_cost_per_1k_tokens"):
            val = getattr(self, attr)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or val < 0:
                raise ValueError(f"{attr} must be a non-negative number")
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise ValueError("currency must be a non-empty string")


def compute_latency_breakdown(run_trace: RunTrace) -> LatencyBreakdown:
    """Compute latency breakdown from measured spans in a RunTrace."""
    if not isinstance(run_trace, RunTrace):
        raise TypeError("run_trace must be a RunTrace")

    def _sum_spans(names: set[str], component: str | None = None) -> float | None:
        vals = [
            s.duration_ms
            for s in run_trace.spans
            if s.duration_ms is not None
            and (s.name in names or (component is not None and s.component == component))
        ]
        if not vals:
            return None
        return round(sum(vals), 3)

    planning_ms = _sum_spans({"planning"}, component="planner")
    retrieval_ms = _sum_spans({"retrieval"})
    llm_ms = _sum_spans({"llm"})
    tools_ms = _sum_spans({"tool"})
    approval_ms = _sum_spans(set(), component="approval")

    total_ms = run_trace.duration_ms
    measured_parts = [
        v for v in (planning_ms, retrieval_ms, llm_ms, tools_ms, approval_ms) if v is not None
    ]

    other_ms: float | None = None
    if total_ms is not None and measured_parts:
        other_ms = round(max(0.0, total_ms - sum(measured_parts)), 3)

    if total_ms is None and not measured_parts:
        mode = "unknown"
    elif total_ms is not None and measured_parts:
        mode = "measured"
    else:
        mode = "partial"

    return LatencyBreakdown(
        total_ms=total_ms,
        planning_ms=planning_ms,
        retrieval_ms=retrieval_ms,
        llm_ms=llm_ms,
        tools_ms=tools_ms,
        approval_ms=approval_ms,
        other_ms=other_ms,
        attribution_mode=mode,
    )


def _classify_error_category(event: str, error_type: str | None, error_msg: str) -> str:
    if error_type and error_type in ERROR_CATEGORIES:
        return error_type
    msg = error_msg.lower()
    if "timeout" in msg or "timed out" in msg:
        return "timeout_error"
    if "maximum allowed size" in msg or "exceeds maximum" in msg:
        return "resource_limit_error"
    if "approval" in msg or event == "approval_denied":
        return "approval_error"
    if event == "retrieval_failed" or "retrieval" in msg:
        return "retrieval_error"
    if event == "llm_failed":
        return "llm_error"
    if event == "tool_failed":
        return "tool_error"
    if "validation" in msg or "unexpected arguments" in msg or "not allowed" in msg:
        return "validation_error"
    if "plan" in msg:
        return "planning_error"
    if event == "step_failed" or event == "task_failed":
        return "execution_error"
    return "unknown_error"


def compute_error_metrics(logs: list[dict[str, Any]]) -> ErrorMetrics:
    """Compute structured error counts, categories, and safe rates."""
    if not isinstance(logs, list):
        raise TypeError("logs must be a list")

    failed_runs = 0
    total_runs = 0
    failed_tasks = 0
    total_tasks = 0
    failed_steps = 0
    total_steps = 0
    failed_tools = 0
    total_tools = 0
    approval_denials = 0
    retrieval_failures = 0
    llm_failures = 0
    timeouts = 0
    resource_limit_failures = 0
    validation_failures = 0
    categories: Counter[str] = Counter()

    for entry in logs:
        if not isinstance(entry, dict):
            continue
        event = entry.get("event", "")
        details = entry.get("details") or entry.get("metadata") or {}
        if not isinstance(details, dict):
            details = {}
        error_type = entry.get("error_type") or details.get("error_type")
        error_msg = str(details.get("error") or entry.get("message") or "")

        if event == "run_started":
            total_runs += 1
        elif event == "run_failed":
            failed_runs += 1
        elif event == "task_started":
            total_tasks += 1
        elif event == "task_failed":
            failed_tasks += 1
        elif event == "step_started":
            total_steps += 1
        elif event == "step_failed":
            failed_steps += 1
        elif event == "tool_called":
            total_tools += 1
        elif event == "tool_failed":
            failed_tools += 1
        elif event == "approval_denied":
            approval_denials += 1
        elif event == "retrieval_failed":
            retrieval_failures += 1
        elif event == "llm_failed":
            llm_failures += 1

        is_error_event = (
            event.endswith("_failed")
            or event == "approval_denied"
            or entry.get("level") == "ERROR"
        )
        if is_error_event:
            cat = _classify_error_category(event, error_type, error_msg)
            categories[cat] += 1
            if cat == "timeout_error":
                timeouts += 1
            elif cat == "resource_limit_error":
                resource_limit_failures += 1
            elif cat == "validation_error":
                validation_failures += 1

    total_errors = sum(categories.values())

    def _rate(num: int, den: int) -> float | None:
        if den <= 0:
            return None
        return round(num / den, 4)

    return ErrorMetrics(
        total_errors=total_errors,
        failed_runs=failed_runs,
        failed_tasks=failed_tasks,
        failed_steps=failed_steps,
        failed_tools=failed_tools,
        approval_denials=approval_denials,
        retrieval_failures=retrieval_failures,
        llm_failures=llm_failures,
        timeouts=timeouts,
        resource_limit_failures=resource_limit_failures,
        validation_failures=validation_failures,
        counts_by_category=dict(sorted(categories.items())),
        step_error_rate=_rate(failed_steps, total_steps),
        tool_error_rate=_rate(failed_tools, total_tools),
        task_error_rate=_rate(failed_tasks, total_tasks),
        run_error_rate=_rate(failed_runs, total_runs),
    )


def compute_token_usage(logs: list[dict[str, Any]]) -> TokenUsage:
    """Aggregate LLM token usage from logs without fabricating unavailable counts."""
    if not isinstance(logs, list):
        raise TypeError("logs must be a list")

    llm_calls = 0
    input_sum = 0
    output_sum = 0
    has_input = False
    has_output = False

    for entry in logs:
        if not isinstance(entry, dict):
            continue
        if entry.get("event") not in {"llm_completed", "llm_failed"}:
            continue

        llm_calls += 1
        details = entry.get("details") or entry.get("metadata") or {}
        if not isinstance(details, dict):
            continue

        inp = details.get("input_tokens")
        out = details.get("output_tokens")

        if isinstance(inp, int) and not isinstance(inp, bool) and inp >= 0:
            input_sum += inp
            has_input = True
        if isinstance(out, int) and not isinstance(out, bool) and out >= 0:
            output_sum += out
            has_output = True

    in_tokens = input_sum if has_input else None
    out_tokens = output_sum if has_output else None
    tot_tokens = (
        (input_sum + output_sum) if (has_input and has_output) else None
    )

    return TokenUsage(
        input_tokens=in_tokens,
        output_tokens=out_tokens,
        total_tokens=tot_tokens,
        llm_calls=llm_calls,
    )


def calculate_cost(
    token_usage: TokenUsage,
    pricing: PricingConfig | None,
) -> float | None:
    """Calculate estimated cost only when explicit pricing and token counts exist."""
    if pricing is None:
        return None
    if not isinstance(pricing, PricingConfig):
        raise TypeError("pricing must be a PricingConfig or None")
    if token_usage.input_tokens is None or token_usage.output_tokens is None:
        return None

    cost = (
        (token_usage.input_tokens / 1000.0) * pricing.input_cost_per_1k_tokens
        + (token_usage.output_tokens / 1000.0) * pricing.output_cost_per_1k_tokens
    )
    return round(cost, 6)
