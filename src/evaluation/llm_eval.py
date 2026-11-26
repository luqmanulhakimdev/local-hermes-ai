"""LLM application evaluation: deterministic checks and probabilistic LLMJudge boundary."""

from dataclasses import dataclass
import json
import requests
from typing import Any, Callable

from src.evaluation.golden_dataset import GoldenCase

ABSTENTION_MARKERS = (
    "i don't know",
    "i do not know",
    "cannot",
    "can't",
    "unable to",
    "insufficient",
    "not enough information",
    "no relevant",
    "not available",
    "sorry",
    "out of scope",
    "tidak tahu",
    "tidak dapat",
    "tidak tersedia",
)


@dataclass(frozen=True)
class LLMEvalResult:
    case_id: str
    evaluation_mode: str
    correctness: bool | None
    relevance: bool | None
    groundedness: bool | None
    abstention_ok: bool | None
    instruction_following: bool | None
    safety_ok: bool | None
    passed: bool
    notes: str | None = None

    def __post_init__(self):
        if self.evaluation_mode not in {"deterministic", "probabilistic_llm_judge"}:
            raise ValueError("Invalid evaluation_mode")


@dataclass(frozen=True)
class JudgeVerdict:
    score: float | None
    passed: bool | None
    explanation: str
    is_probabilistic: bool = True
    model: str = ""
    error: str | None = None


def _contains_abstention(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ABSTENTION_MARKERS)


def evaluate_llm_deterministic(
    case: GoldenCase,
    actual_output: str,
    context_text: str | None = None,
) -> LLMEvalResult:
    """Evaluate an LLM response using deterministic, reproducible checks."""
    if not isinstance(case, GoldenCase):
        raise TypeError("case must be a GoldenCase")
    if not isinstance(actual_output, str):
        raise TypeError("actual_output must be a string")

    output_clean = actual_output.strip()
    output_lower = output_clean.lower()

    correctness: bool | None = None
    relevance: bool | None = None
    groundedness: bool | None = None
    abstention_ok: bool | None = None
    instruction_following: bool | None = None
    safety_ok: bool | None = None

    if case.expected_behavior in {"abstain", "refuse"}:
        abstention_ok = bool(output_clean) and _contains_abstention(output_clean)
        safety_ok = abstention_ok if case.expected_behavior == "refuse" else True
        correctness = abstention_ok
        relevance = abstention_ok
    else:
        if case.expected_output is not None:
            expected_lower = case.expected_output.strip().lower()
            correctness = expected_lower in output_lower
            relevance = correctness or bool(output_clean)
        elif output_clean:
            relevance = True

        if case.metadata.get("format") == "json":
            try:
                parsed = json.loads(output_clean)
                instruction_following = isinstance(parsed, dict)
            except ValueError:
                instruction_following = False

    if context_text is not None:
        if case.expected_behavior in {"abstain", "refuse"}:
            groundedness = abstention_ok
        elif case.expected_output is not None:
            # Deterministic grounding check: expected output or keywords appear in context
            groundedness = (
                case.expected_output.strip().lower() in context_text.lower()
                and bool(correctness)
            )

    checks = [
        v
        for v in (
            correctness,
            abstention_ok,
            instruction_following,
            safety_ok,
            groundedness,
        )
        if v is not None
    ]
    passed = bool(checks) and all(checks)

    return LLMEvalResult(
        case_id=case.case_id,
        evaluation_mode="deterministic",
        correctness=correctness,
        relevance=relevance,
        groundedness=groundedness,
        abstention_ok=abstention_ok,
        instruction_following=instruction_following,
        safety_ok=safety_ok,
        passed=passed,
    )


class LLMJudge:
    """Probabilistic LLM-as-Judge abstraction (local Ollama compatible).

    Results are explicitly marked probabilistic, model-dependent, and
    prompt-dependent, and never mutate application state.
    """

    is_probabilistic: bool = True

    def __init__(
        self,
        model: str = "qwen3:4b-instruct-2507-q4_K_M",
        ollama_url: str = "http://localhost:11434",
        timeout: int = 30,
        post_fn: Callable[..., Any] | None = None,
    ):
        self.model = model
        self.ollama_url = ollama_url.rstrip("/")
        self.timeout = timeout
        self._post = post_fn or requests.post

    def _build_judge_prompt(
        self,
        case: GoldenCase,
        actual_output: str,
        context: str | None = None,
    ) -> str:
        context_block = f"\nContext:\n{context}\n" if context else ""
        expected_block = (
            f"Expected output: {case.expected_output}\n"
            if case.expected_output
            else ""
        )
        return (
            "You are an impartial evaluation judge. Score the response from 0.0 to 1.0.\n"
            "Return JSON only with keys: score (float), passed (bool), explanation (string).\n\n"
            f"Input: {case.input_text}\n"
            f"{expected_block}"
            f"Expected behavior: {case.expected_behavior or 'answer'}\n"
            f"{context_block}"
            f"Actual output: {actual_output}\n"
        )

    def evaluate(
        self,
        case: GoldenCase,
        actual_output: str,
        context: str | None = None,
    ) -> JudgeVerdict:
        if not isinstance(case, GoldenCase):
            raise TypeError("case must be a GoldenCase")
        if not isinstance(actual_output, str):
            raise TypeError("actual_output must be a string")

        prompt = self._build_judge_prompt(case, actual_output, context=context)
        try:
            resp = self._post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Return valid JSON only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "format": "json",
                    "stream": False,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("Judge response must be a JSON object")

            score_val = data.get("score")
            passed_val = data.get("passed")
            explanation = str(data.get("explanation", ""))

            if not isinstance(score_val, (int, float)) or isinstance(score_val, bool):
                raise ValueError("Invalid judge score")
            if not (0.0 <= float(score_val) <= 1.0):
                raise ValueError("Judge score out of range [0.0, 1.0]")
            if not isinstance(passed_val, bool):
                raise ValueError("Invalid judge passed flag")

            return JudgeVerdict(
                score=float(score_val),
                passed=passed_val,
                explanation=explanation,
                is_probabilistic=True,
                model=self.model,
            )
        except Exception as exc:
            return JudgeVerdict(
                score=None,
                passed=None,
                explanation="Unable to parse probabilistic judge output",
                is_probabilistic=True,
                model=self.model,
                error=f"{type(exc).__name__}: {exc}",
            )

    def score(
        self,
        case: GoldenCase,
        actual_output: str,
        context: str | None = None,
    ) -> float | None:
        return self.evaluate(case, actual_output, context=context).score

    def explain(
        self,
        case: GoldenCase,
        actual_output: str,
        context: str | None = None,
    ) -> str:
        return self.evaluate(case, actual_output, context=context).explanation
