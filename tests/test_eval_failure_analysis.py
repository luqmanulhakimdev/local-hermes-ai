import unittest

from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.evaluation.failure_analysis import analyze_failure, cluster_failures
from src.evaluation.golden_dataset import GoldenCase
from src.evaluation.rag_eval import RAGEvalResult
from src.evaluation.trajectory_eval import TrajectoryEvalResult


class TestFailureAnalysis(unittest.TestCase):
    def test_retrieval_error_and_observed_vs_inferred(self):
        case = GoldenCase(
            case_id="rag_1",
            category="rag",
            input_text="What is a token?",
            expected_sources=["llm-basics.md"],
        )
        rag_res = RAGEvalResult(
            case_id="rag_1",
            retrieval_success=False,
            expected_sources_present=False,
            grounding_success=None,
            abstention_success=None,
            source_attribution_ok=False,
            failure_stage="retrieval_failure",
            passed=False,
        )
        report = analyze_failure(
            case=case,
            actual_summary="Retrieved wrong file",
            rag_result=rag_res,
        )
        self.assertEqual(report.failure_category, "retrieval_error")
        self.assertEqual(report.suggested_area, "rag_retriever")
        self.assertIn("Observed outcome: Retrieved wrong file", report.observed_facts)
        self.assertIn("Expected sources were not present", " ".join(report.observed_facts))
        self.assertTrue(bool(report.inferred_root_cause))

    def test_unknown_category_when_insufficient_evidence(self):
        case = GoldenCase(
            case_id="auto_unk",
            category="automation",
            input_text="Do something",
        )
        report = analyze_failure(case=case, actual_summary="Unexpected state")
        self.assertEqual(report.failure_category, "unknown")
        self.assertEqual(report.confidence, "low")

    def test_failure_clustering(self):
        c1 = GoldenCase(case_id="c1", category="rag", input_text="q1")
        c2 = GoldenCase(case_id="c2", category="rag", input_text="q2")
        c3 = GoldenCase(case_id="c3", category="security", input_text="bad")

        rag_miss = RAGEvalResult(
            case_id="c1",
            retrieval_success=False,
            expected_sources_present=False,
            grounding_success=None,
            abstention_success=None,
            source_attribution_ok=False,
            failure_stage="retrieval_failure",
            passed=False,
        )
        r1 = analyze_failure(c1, "miss", rag_result=rag_miss)
        r2 = analyze_failure(c2, "miss", rag_result=rag_miss)
        r3 = analyze_failure(c3, "bypassed", error_message="Unauthorized")

        summary = cluster_failures([r1, r2, r3])
        self.assertEqual(summary.total_failures, 3)
        self.assertEqual(summary.counts_by_category["retrieval_error"], 2)
        self.assertEqual(summary.counts_by_category["safety_violation"], 1)
        self.assertEqual(summary.most_frequent_category, "retrieval_error")
        self.assertEqual(summary.affected_cases_by_category["retrieval_error"], ("c1", "c2"))


if __name__ == "__main__":
    unittest.main()
