"""Focused RAG evaluation distinguishing retrieval failures from grounding failures."""

from dataclasses import dataclass

from src.evaluation.golden_dataset import GoldenCase
from src.evaluation.llm_eval import _contains_abstention
from src.rag.evaluation import keyword_coverage


@dataclass(frozen=True)
class RAGEvalResult:
    case_id: str
    retrieval_success: bool
    expected_sources_present: bool
    grounding_success: bool | None
    abstention_success: bool | None
    source_attribution_ok: bool
    failure_stage: str | None
    passed: bool


def evaluate_rag_pipeline_case(
    case: GoldenCase,
    retrieved_chunks: list[dict],
    answer: str,
    cited_sources: list[str] | None = None,
) -> RAGEvalResult:
    """Evaluate retrieval, grounding, abstention, and source attribution for a RAG case."""
    if not isinstance(case, GoldenCase):
        raise TypeError("case must be a GoldenCase")
    if not isinstance(retrieved_chunks, list):
        raise TypeError("retrieved_chunks must be a list of dicts")
    if not isinstance(answer, str):
        raise TypeError("answer must be a string")

    retrieved_sources = {
        c.get("source", "") for c in retrieved_chunks if isinstance(c, dict)
    }
    expected_sources = set(case.expected_sources)

    # Negative / abstention cases
    if case.expected_behavior == "abstain":
        retrieval_success = len(retrieved_chunks) == 0 or not expected_sources
        expected_sources_present = True
        abstention_success = bool(answer.strip()) and _contains_abstention(answer)
        grounding_success = abstention_success
        source_attribution_ok = True
        failure_stage = None if abstention_success else "abstention_failure"
        return RAGEvalResult(
            case_id=case.case_id,
            retrieval_success=retrieval_success,
            expected_sources_present=expected_sources_present,
            grounding_success=grounding_success,
            abstention_success=abstention_success,
            source_attribution_ok=source_attribution_ok,
            failure_stage=failure_stage,
            passed=abstention_success,
        )

    # Answerable cases
    expected_sources_present = (
        expected_sources.issubset(retrieved_sources)
        if expected_sources
        else len(retrieved_chunks) > 0
    )
    retrieval_success = expected_sources_present

    if not retrieval_success:
        return RAGEvalResult(
            case_id=case.case_id,
            retrieval_success=False,
            expected_sources_present=False,
            grounding_success=None,
            abstention_success=None,
            source_attribution_ok=False,
            failure_stage="retrieval_failure",
            passed=False,
        )

    # Retrieval succeeded -> evaluate grounding & attribution
    context_text = " ".join(
        str(c.get("content", "")) for c in retrieved_chunks if isinstance(c, dict)
    )
    expected_keywords = case.metadata.get("expected_keywords", [])
    if expected_keywords:
        cov = keyword_coverage(answer, expected_keywords)
        grounding_success = cov >= 0.5 and not _contains_abstention(answer)
    elif case.expected_output:
        grounding_success = (
            case.expected_output.lower() in answer.lower()
            and case.expected_output.lower() in context_text.lower()
        )
    else:
        grounding_success = bool(answer.strip()) and not _contains_abstention(answer)

    if cited_sources is not None:
        source_attribution_ok = (
            expected_sources.issubset(set(cited_sources))
            if expected_sources
            else len(cited_sources) > 0
        )
    else:
        source_attribution_ok = True

    passed = retrieval_success and bool(grounding_success) and source_attribution_ok
    failure_stage = None
    if not grounding_success:
        failure_stage = "grounding_failure"
    elif not source_attribution_ok:
        failure_stage = "attribution_failure"

    return RAGEvalResult(
        case_id=case.case_id,
        retrieval_success=retrieval_success,
        expected_sources_present=expected_sources_present,
        grounding_success=grounding_success,
        abstention_success=None,
        source_attribution_ok=source_attribution_ok,
        failure_stage=failure_stage,
        passed=passed,
    )
