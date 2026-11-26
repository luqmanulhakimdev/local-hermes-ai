import json
import unittest
from unittest.mock import MagicMock

from src.evaluation.golden_dataset import GoldenCase
from src.evaluation.llm_eval import LLMJudge, evaluate_llm_deterministic


class TestLLMEvaluation(unittest.TestCase):
    def test_deterministic_correct_and_incorrect_output(self):
        case = GoldenCase(
            case_id="llm_1",
            category="llm",
            input_text="Capital of France?",
            expected_output="Paris",
            expected_behavior="answer",
        )
        res_ok = evaluate_llm_deterministic(case, "The capital is Paris.")
        self.assertTrue(res_ok.passed)
        self.assertTrue(res_ok.correctness)
        self.assertEqual(res_ok.evaluation_mode, "deterministic")

        res_bad = evaluate_llm_deterministic(case, "The capital is London.")
        self.assertFalse(res_bad.passed)
        self.assertFalse(res_bad.correctness)

    def test_deterministic_json_instruction_following(self):
        case = GoldenCase(
            case_id="llm_json",
            category="llm",
            input_text="Return JSON",
            expected_output='{"status": "ok"}',
            expected_behavior="answer",
            metadata={"format": "json"},
        )
        res_valid = evaluate_llm_deterministic(case, '{"status": "ok"}')
        self.assertTrue(res_valid.instruction_following)
        self.assertTrue(res_valid.passed)

        res_invalid = evaluate_llm_deterministic(case, "not json")
        self.assertFalse(res_invalid.instruction_following)
        self.assertFalse(res_invalid.passed)

    def test_deterministic_abstention_and_refusal(self):
        case = GoldenCase(
            case_id="llm_abs",
            category="llm",
            input_text="What is the secret passcode?",
            expected_behavior="abstain",
        )
        res_abs = evaluate_llm_deterministic(case, "I do not know the passcode.")
        self.assertTrue(res_abs.abstention_ok)
        self.assertTrue(res_abs.passed)

        res_hallucinated = evaluate_llm_deterministic(case, "The passcode is 1234.")
        self.assertFalse(res_hallucinated.abstention_ok)
        self.assertFalse(res_hallucinated.passed)

    def test_deterministic_groundedness_check(self):
        case = GoldenCase(
            case_id="rag_1",
            category="rag",
            input_text="What is a token?",
            expected_output="token",
            expected_behavior="answer",
        )
        res_grounded = evaluate_llm_deterministic(
            case,
            "A token is a unit of text.",
            context_text="In LLMs, a token is the basic unit of text.",
        )
        self.assertTrue(res_grounded.groundedness)
        self.assertTrue(res_grounded.passed)

        res_unsupported = evaluate_llm_deterministic(
            case,
            "A token is a unit of text.",
            context_text="Unrelated cooking recipe.",
        )
        self.assertFalse(res_unsupported.groundedness)
        self.assertFalse(res_unsupported.passed)

    def test_llm_judge_probabilistic_and_malformed_safeguard(self):
        case = GoldenCase(
            case_id="llm_1",
            category="llm",
            input_text="Capital of France?",
            expected_output="Paris",
        )

        mock_post = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {
                "content": json.dumps({
                    "score": 0.95,
                    "passed": True,
                    "explanation": "Accurate answer.",
                })
            }
        }
        mock_post.return_value = mock_resp

        judge = LLMJudge(post_fn=mock_post)
        verdict = judge.evaluate(case, "Paris")
        self.assertTrue(verdict.is_probabilistic)
        self.assertEqual(verdict.score, 0.95)
        self.assertTrue(verdict.passed)
        self.assertIsNone(verdict.error)

        # Malformed output safeguard
        mock_resp.json.return_value = {"message": {"content": "not valid json"}}
        bad_verdict = judge.evaluate(case, "Paris")
        self.assertTrue(bad_verdict.is_probabilistic)
        self.assertIsNone(bad_verdict.score)
        self.assertIsNone(bad_verdict.passed)
        self.assertIsNotNone(bad_verdict.error)


if __name__ == "__main__":
    unittest.main()
