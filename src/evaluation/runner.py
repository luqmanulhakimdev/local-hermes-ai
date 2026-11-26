"""Unified evaluation runner and readable terminal report generator."""

from dataclasses import dataclass

from src.evaluation.failure_analysis import (
    FailureClusterSummary,
    FailureReport,
    cluster_failures,
)
from src.evaluation.golden_dataset import GoldenDataset
from src.evaluation.llm_eval import LLMEvalResult
from src.evaluation.rag_eval import RAGEvalResult
from src.evaluation.regression import RegressionComparisonReport, compare_regression
from src.evaluation.trajectory_eval import TrajectoryEvalResult


@dataclass(frozen=True)
class EvaluationRunResult:
    dataset_name: str
    dataset_version: str
    evaluation_mode: str  # "deterministic" or "live"
    model_name: str | None
    total_cases: int
    llm_results: tuple[LLMEvalResult, ...]
    trajectory_results: tuple[TrajectoryEvalResult, ...]
    rag_results: tuple[RAGEvalResult, ...]
    regression_report: RegressionComparisonReport | None
    failure_reports: tuple[FailureReport, ...]
    failure_summary: FailureClusterSummary
    overall_status: str  # "PASS", "FAIL", "WARNING"

    def aggregate_metrics(self) -> dict[str, float | None]:
        """Compute deterministic aggregate metrics; None when evidence is absent."""
        def _rate(vals: list[bool | None]) -> float | None:
            present = [v for v in vals if v is not None]
            if not present:
                return None
            return round(sum(1 for v in present if v) / len(present), 4)

        return {
            "llm_correctness": _rate([r.correctness for r in self.llm_results]),
            "llm_relevance": _rate([r.relevance for r in self.llm_results]),
            "llm_groundedness": _rate([r.groundedness for r in self.llm_results]),
            "llm_abstention": _rate([r.abstention_ok for r in self.llm_results]),
            "agent_planning": _rate(
                [r.step_count_correct and r.step_ordering_correct for r in self.trajectory_results]
            ),
            "agent_tool_selection": _rate(
                [r.tool_selection_correct for r in self.trajectory_results]
            ),
            "agent_trajectory": _rate(
                [r.trajectory_passed for r in self.trajectory_results]
            ),
            "agent_approval": _rate(
                [r.approval_compliant for r in self.trajectory_results]
            ),
            "agent_execution": _rate(
                [r.final_outcome_correct for r in self.trajectory_results]
            ),
            "agent_recovery": _rate(
                [r.recovery_ok for r in self.trajectory_results]
            ),
            "rag_retrieval": _rate([r.retrieval_success for r in self.rag_results]),
            "rag_groundedness": _rate([r.grounding_success for r in self.rag_results]),
            "rag_attribution": _rate([r.source_attribution_ok for r in self.rag_results]),
        }


class EvaluationRunner:
    """Orchestrates evaluation collection, failure clustering, regression comparison, and reporting."""

    def __init__(
        self,
        dataset: GoldenDataset,
        evaluation_mode: str = "deterministic",
        model_name: str | None = None,
    ):
        if not isinstance(dataset, GoldenDataset):
            raise TypeError("dataset must be a GoldenDataset")
        if evaluation_mode not in {"deterministic", "live"}:
            raise ValueError("evaluation_mode must be 'deterministic' or 'live'")
        self.dataset = dataset
        self.evaluation_mode = evaluation_mode
        self.model_name = model_name

    def compile_run(
        self,
        llm_results: list[LLMEvalResult] | None = None,
        trajectory_results: list[TrajectoryEvalResult] | None = None,
        rag_results: list[RAGEvalResult] | None = None,
        failure_reports: list[FailureReport] | None = None,
        baseline_metrics: dict[str, float | None] | None = None,
        allowed_drop: float = 0.02,
    ) -> EvaluationRunResult:
        llm_tuple = tuple(llm_results or [])
        traj_tuple = tuple(trajectory_results or [])
        rag_tuple = tuple(rag_results or [])
        failures_list = list(failure_reports or [])
        failure_summary = cluster_failures(failures_list)

        tentative = EvaluationRunResult(
            dataset_name=self.dataset.name,
            dataset_version=self.dataset.version,
            evaluation_mode=self.evaluation_mode,
            model_name=self.model_name,
            total_cases=len(self.dataset.cases),
            llm_results=llm_tuple,
            trajectory_results=traj_tuple,
            rag_results=rag_tuple,
            regression_report=None,
            failure_reports=tuple(failures_list),
            failure_summary=failure_summary,
            overall_status="PASS",
        )

        reg_report = None
        if baseline_metrics is not None:
            reg_report = compare_regression(
                baseline=baseline_metrics,
                current=tentative.aggregate_metrics(),
                allowed_drop=allowed_drop,
            )

        has_failure = bool(failures_list) or (
            reg_report is not None and reg_report.overall_status == "REGRESSION"
        )
        has_warning = reg_report is not None and reg_report.overall_status == "WARNING"

        if has_failure:
            overall = "FAIL"
        elif has_warning:
            overall = "WARNING"
        else:
            overall = "PASS"

        return EvaluationRunResult(
            dataset_name=self.dataset.name,
            dataset_version=self.dataset.version,
            evaluation_mode=self.evaluation_mode,
            model_name=self.model_name,
            total_cases=len(self.dataset.cases),
            llm_results=llm_tuple,
            trajectory_results=traj_tuple,
            rag_results=rag_tuple,
            regression_report=reg_report,
            failure_reports=tuple(failures_list),
            failure_summary=failure_summary,
            overall_status=overall,
        )

    @staticmethod
    def format_report(result: EvaluationRunResult) -> str:
        """Format a readable terminal evaluation report without fabricating missing metrics."""
        metrics = result.aggregate_metrics()

        def _fmt(val: float | None) -> str:
            return "N/A" if val is None else f"{val:.2f}"

        reg = result.regression_report
        reg_lines = (
            [
                f"Improved: {reg.improved_count}",
                f"Unchanged: {reg.unchanged_count}",
                f"Regressed: {reg.regressed_count}",
                f"Unknown: {reg.unknown_count}",
            ]
            if reg is not None
            else ["NOT RUN"]
        )

        counts = result.failure_summary.counts_by_category
        failure_lines = (
            [f"{cat}: {cnt}" for cat, cnt in counts.items()]
            if counts
            else ["None"]
        )

        model_info = result.model_name or "N/A (deterministic)"

        return "\n".join(
            [
                "==================================================",
                "AI ENGINEERING EVALUATION",
                "==================================================",
                "",
                f"Dataset: {result.dataset_name} (v{result.dataset_version})",
                f"Cases: {result.total_cases}",
                f"Mode: {result.evaluation_mode}",
                f"Model: {model_info}",
                "",
                "LLM Application (Deterministic)",
                "-------------------------------",
                f"Correctness: {_fmt(metrics['llm_correctness'])}",
                f"Relevance: {_fmt(metrics['llm_relevance'])}",
                f"Groundedness: {_fmt(metrics['llm_groundedness'])}",
                f"Abstention: {_fmt(metrics['llm_abstention'])}",
                "",
                "Agent (Deterministic Trajectory)",
                "--------------------------------",
                f"Planning: {_fmt(metrics['agent_planning'])}",
                f"Tool Selection: {_fmt(metrics['agent_tool_selection'])}",
                f"Trajectory: {_fmt(metrics['agent_trajectory'])}",
                f"Approval: {_fmt(metrics['agent_approval'])}",
                f"Execution: {_fmt(metrics['agent_execution'])}",
                f"Recovery: {_fmt(metrics['agent_recovery'])}",
                "",
                "RAG (Deterministic)",
                "-------------------",
                f"Retrieval: {_fmt(metrics['rag_retrieval'])}",
                f"Groundedness: {_fmt(metrics['rag_groundedness'])}",
                f"Source Attribution: {_fmt(metrics['rag_attribution'])}",
                "",
                "Regression",
                "----------",
                *reg_lines,
                "",
                "Failures",
                "--------",
                *failure_lines,
                "",
                f"Overall: {result.overall_status}",
                "==================================================",
            ]
        )
