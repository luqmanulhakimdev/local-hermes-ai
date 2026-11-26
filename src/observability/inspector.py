"""Run inspection, filtering, and readable observability summary reporting."""

from dataclasses import dataclass
from typing import Any

from src.automation.models import TaskPlan
from src.observability.metrics import (
    ErrorMetrics,
    LatencyBreakdown,
    PricingConfig,
    TokenUsage,
    calculate_cost,
    compute_error_metrics,
    compute_latency_breakdown,
    compute_token_usage,
)
from src.observability.tracing import RunTrace, build_run_trace

MAX_SUMMARY_OUTPUT_LEN = 200


def _truncate_output(val: Any, max_len: int = MAX_SUMMARY_OUTPUT_LEN) -> str | None:
    if val is None:
        return None
    text = str(val)
    if len(text) > max_len:
        return text[:max_len] + "... [TRUNCATED]"
    return text


@dataclass(frozen=True)
class InspectedStep:
    step_id: int
    tool: str
    status: str
    duration_ms: float | None
    approval_status: str | None
    output_summary: str | None
    error: str | None


@dataclass(frozen=True)
class RunInspectionReport:
    run_id: str
    task_id: str | None
    status: str
    start_time: str | None
    end_time: str | None
    model: str | None
    provider: str | None
    trace: RunTrace
    latency: LatencyBreakdown
    errors: ErrorMetrics
    token_usage: TokenUsage
    estimated_cost: float | None
    currency: str | None
    steps: tuple[InspectedStep, ...]


class RunInspector:
    """Inspect and search AI runs from structured observability logs and optional TaskPlan."""

    def inspect_run(
        self,
        run_id: str,
        logs: list[dict[str, Any]],
        task: TaskPlan | None = None,
        pricing: PricingConfig | None = None,
        model: str | None = None,
        provider: str | None = None,
    ) -> RunInspectionReport | None:
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        if not isinstance(logs, list):
            raise TypeError("logs must be a list")

        run_logs = [
            e
            for e in logs
            if isinstance(e, dict)
            and (
                e.get("run_id") == run_id
                or (
                    isinstance(e.get("details"), dict)
                    and e["details"].get("run_id") == run_id
                )
                or (e.get("run_id") is None and e.get("task_id") == run_id)
            )
        ]

        if not run_logs:
            return None

        trace = build_run_trace(run_id=run_id, logs=run_logs)
        latency = compute_latency_breakdown(trace)
        errors = compute_error_metrics(run_logs)
        tokens = compute_token_usage(run_logs)
        cost = calculate_cost(tokens, pricing)

        detected_model = model
        detected_provider = provider
        for entry in run_logs:
            details = entry.get("details") or entry.get("metadata") or {}
            if isinstance(details, dict):
                if detected_model is None and details.get("model"):
                    detected_model = str(details["model"])
                if detected_provider is None and details.get("provider"):
                    detected_provider = str(details["provider"])

        # Build step summaries
        step_spans = {s.step_id: s for s in trace.spans if s.name.startswith("step_")}
        approval_spans = {
            s.step_id: s for s in trace.spans if s.name.startswith("approval_")
        }

        inspected_steps: list[InspectedStep] = []
        if task is not None:
            for step in task.steps:
                sp = step_spans.get(step.step_id)
                ap = approval_spans.get(step.step_id)
                inspected_steps.append(
                    InspectedStep(
                        step_id=step.step_id,
                        tool=step.tool,
                        status=step.status.value,
                        duration_ms=sp.duration_ms if sp else None,
                        approval_status=ap.status if ap else None,
                        output_summary=_truncate_output(step.output),
                        error=step.error,
                    )
                )
        elif trace.task_trace is not None:
            for step_id, st in sorted(trace.task_trace.steps.items()):
                sp = step_spans.get(step_id)
                ap = approval_spans.get(step_id)
                ap_status = ap.status if ap else (
                    "granted"
                    if st.approval_granted
                    else ("denied" if st.approval_denied else ("requested" if st.approval_requested else None))
                )
                status = (
                    "completed"
                    if st.completed
                    else ("failed" if st.failed else "started")
                )
                inspected_steps.append(
                    InspectedStep(
                        step_id=step_id,
                        tool=st.tool or "unknown",
                        status=status,
                        duration_ms=sp.duration_ms if sp else None,
                        approval_status=ap_status,
                        output_summary=_truncate_output(st.output),
                        error=st.error,
                    )
                )

        return RunInspectionReport(
            run_id=run_id,
            task_id=trace.task_id,
            status=trace.status,
            start_time=trace.start_time,
            end_time=trace.end_time,
            model=detected_model,
            provider=detected_provider,
            trace=trace,
            latency=latency,
            errors=errors,
            token_usage=tokens,
            estimated_cost=cost,
            currency=pricing.currency if pricing else None,
            steps=tuple(inspected_steps),
        )

    def search_runs(
        self,
        logs: list[dict[str, Any]],
        run_id: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
        error_category: str | None = None,
    ) -> list[str]:
        """Return matching run IDs filtered by criteria."""
        if not isinstance(logs, list):
            raise TypeError("logs must be a list")

        candidate_ids: list[str] = []
        seen: set[str] = set()
        for entry in logs:
            if not isinstance(entry, dict):
                continue
            details = entry.get("details") or {}
            rid = (
                entry.get("run_id")
                or (details.get("run_id") if isinstance(details, dict) else None)
                or entry.get("task_id")
            )
            if isinstance(rid, str) and rid.strip() and rid not in seen:
                seen.add(rid)
                candidate_ids.append(rid)

        matched: list[str] = []
        for rid in candidate_ids:
            if run_id is not None and rid != run_id:
                continue
            report = self.inspect_run(rid, logs)
            if report is None:
                continue
            if task_id is not None and report.task_id != task_id:
                continue
            if status is not None and report.status != status:
                continue
            if error_category is not None and error_category not in report.errors.counts_by_category:
                continue
            matched.append(rid)

        return matched


def format_observability_summary(report: RunInspectionReport) -> str:
    """Format a readable terminal summary using N/A or UNKNOWN when evidence is missing."""
    if not isinstance(report, RunInspectionReport):
        raise TypeError("report must be a RunInspectionReport")

    def _ms(val: float | None) -> str:
        return "N/A" if val is None else f"{val:.1f}ms"

    def _int(val: int | None) -> str:
        return "N/A" if val is None else str(val)

    cost_str = (
        "UNKNOWN"
        if report.estimated_cost is None
        else f"{report.estimated_cost:.6f} {report.currency or ''}".strip()
    )

    cats = report.errors.counts_by_category
    total_steps = len(report.steps)
    completed_steps = sum(1 for s in report.steps if s.status == "completed")
    failed_steps = sum(1 for s in report.steps if s.status == "failed")

    return "\n".join(
        [
            "==================================================",
            "OBSERVABILITY SUMMARY",
            "==================================================",
            "",
            "Run:",
            f"  ID: {report.run_id}",
            f"  Status: {report.status}",
            f"  Duration: {_ms(report.latency.total_ms)}",
            f"  Model: {report.model or 'UNKNOWN'}",
            f"  Lifecycle valid: {report.trace.lifecycle_valid}",
            "",
            "LLM:",
            f"  Calls: {report.token_usage.llm_calls}",
            f"  Input tokens: {_int(report.token_usage.input_tokens)}",
            f"  Output tokens: {_int(report.token_usage.output_tokens)}",
            f"  Total tokens: {_int(report.token_usage.total_tokens)}",
            f"  Estimated cost: {cost_str}",
            "",
            "Latency:",
            f"  Planning: {_ms(report.latency.planning_ms)}",
            f"  Retrieval: {_ms(report.latency.retrieval_ms)}",
            f"  LLM: {_ms(report.latency.llm_ms)}",
            f"  Tools: {_ms(report.latency.tools_ms)}",
            f"  Approval: {_ms(report.latency.approval_ms)}",
            f"  Total: {_ms(report.latency.total_ms)}",
            "",
            "Errors:",
            f"  Total: {report.errors.total_errors}",
            f"  Validation: {cats.get('validation_error', 0)}",
            f"  Planning: {cats.get('planning_error', 0)}",
            f"  Retrieval: {cats.get('retrieval_error', 0)}",
            f"  Tool: {cats.get('tool_error', 0)}",
            f"  LLM: {cats.get('llm_error', 0)}",
            f"  Approval: {cats.get('approval_error', 0)}",
            f"  Timeout: {cats.get('timeout_error', 0)}",
            "",
            "Steps:",
            f"  Total: {total_steps}",
            f"  Completed: {completed_steps}",
            f"  Failed: {failed_steps}",
            "",
            "==================================================",
        ]
    )
