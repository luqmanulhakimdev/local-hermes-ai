import unittest

from src.evaluation.golden_dataset import GoldenCase
from src.evaluation.rag_eval import evaluate_rag_pipeline_case


class TestRAGPipelineEvaluation(unittest.TestCase):
    def test_successful_retrieval_and_grounded_answer(self):
        case = GoldenCase(
            case_id="rag_1",
            category="rag",
            input_text="What is a token?",
            expected_output="token",
            expected_behavior="answer",
            expected_sources=["llm-basics.md"],
            metadata={"expected_keywords": ["token", "text"]},
        )
        chunks = [{"source": "llm-basics.md", "content": "A token is a unit of text."}]
        res = evaluate_rag_pipeline_case(
            case,
            retrieved_chunks=chunks,
            answer="A token is a basic unit of text.",
            cited_sources=["llm-basics.md"],
        )
        self.assertTrue(res.passed)
        self.assertTrue(res.retrieval_success)
        self.assertTrue(res.grounding_success)
        self.assertTrue(res.source_attribution_ok)
        self.assertIsNone(res.failure_stage)

    def test_retrieval_failure_distinguished_from_grounding_failure(self):
        case = GoldenCase(
            case_id="rag_1",
            category="rag",
            input_text="What is a token?",
            expected_output="token",
            expected_behavior="answer",
            expected_sources=["llm-basics.md"],
            metadata={"expected_keywords": ["token", "text"]},
        )
        # Retrieval miss
        res_ret_miss = evaluate_rag_pipeline_case(
            case,
            retrieved_chunks=[{"source": "other.md", "content": "Unrelated"}],
            answer="A token is a unit of text.",
        )
        self.assertFalse(res_ret_miss.passed)
        self.assertFalse(res_ret_miss.retrieval_success)
        self.assertEqual(res_ret_miss.failure_stage, "retrieval_failure")

        # Retrieval hit, but answer ignores context (abstains or misses keywords)
        res_ground_miss = evaluate_rag_pipeline_case(
            case,
            retrieved_chunks=[{"source": "llm-basics.md", "content": "A token is a unit of text."}],
            answer="I do not know.",
        )
        self.assertFalse(res_ground_miss.passed)
        self.assertTrue(res_ground_miss.retrieval_success)
        self.assertFalse(res_ground_miss.grounding_success)
        self.assertEqual(res_ground_miss.failure_stage, "grounding_failure")

    def test_rag_abstention_case(self):
        case = GoldenCase(
            case_id="rag_neg",
            category="rag",
            input_text="Capital of Japan?",
            expected_behavior="abstain",
            expected_sources=[],
        )
        res_ok = evaluate_rag_pipeline_case(
            case,
            retrieved_chunks=[],
            answer="Insufficient context in project documents.",
        )
        self.assertTrue(res_ok.passed)
        self.assertTrue(res_ok.abstention_success)

        res_bad = evaluate_rag_pipeline_case(
            case,
            retrieved_chunks=[],
            answer="The capital is Tokyo.",
        )
        self.assertFalse(res_bad.passed)
        self.assertEqual(res_bad.failure_stage, "abstention_failure")


if __name__ == "__main__":
    unittest.main()
