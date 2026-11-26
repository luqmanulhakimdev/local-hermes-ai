"""AI Engineering Evaluation framework for Local Hermes AI."""

from src.evaluation.failure_analysis import (
    FAILURE_CATEGORIES,
    FailureClusterSummary,
    FailureReport,
    analyze_failure,
    cluster_failures,
)
from src.evaluation.golden_dataset import (
    AUTOMATION_GOLDEN_CASES,
    DEFAULT_GOLDEN_DATASET,
    LLM_GOLDEN_CASES,
    RAG_GOLDEN_CASES,
    SECURITY_GOLDEN_CASES,
    GoldenCase,
    GoldenDataset,
)
from src.evaluation.llm_eval import (
    JudgeVerdict,
    LLMEvalResult,
    LLMJudge,
    evaluate_llm_deterministic,
)
from src.evaluation.rag_eval import RAGEvalResult, evaluate_rag_pipeline_case
from src.evaluation.regression import (
    MetricComparison,
    RegressionComparisonReport,
    compare_regression,
)
from src.evaluation.runner import EvaluationRunResult, EvaluationRunner
from src.evaluation.trajectory_eval import (
    TrajectoryEvalResult,
    TrajectoryStepSummary,
    evaluate_trajectory,
)

__all__ = [
    "FAILURE_CATEGORIES",
    "FailureClusterSummary",
    "FailureReport",
    "analyze_failure",
    "cluster_failures",
    "AUTOMATION_GOLDEN_CASES",
    "DEFAULT_GOLDEN_DATASET",
    "LLM_GOLDEN_CASES",
    "RAG_GOLDEN_CASES",
    "SECURITY_GOLDEN_CASES",
    "GoldenCase",
    "GoldenDataset",
    "JudgeVerdict",
    "LLMEvalResult",
    "LLMJudge",
    "evaluate_llm_deterministic",
    "RAGEvalResult",
    "evaluate_rag_pipeline_case",
    "MetricComparison",
    "RegressionComparisonReport",
    "compare_regression",
    "EvaluationRunResult",
    "EvaluationRunner",
    "TrajectoryEvalResult",
    "TrajectoryStepSummary",
    "evaluate_trajectory",
]
