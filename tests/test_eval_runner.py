import unittest

from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.evaluation.golden_dataset import DEFAULT_GOLDEN_DATASET, SECURITY_GOLDEN_CASES
from src.evaluation.llm_eval import evaluate_llm_deterministic
from src.evaluation.rag_eval import evaluate_rag_pipeline_case
from src.evaluation.runner import EvaluationRunner
from src.evaluation.trajectory_eval import evaluate_trajectory


class TestEvaluationRunner(unittest.TestCase):
    def test_runner_compile_and_format_report_without_fabricating_metrics(self):
        runner = EvaluationRunner(
            dataset=DEFAULT_GOLDEN_DATASET,
            evaluation_mode="deterministic",
        )
        llm_case = DEFAULT_GOLDEN_DATASET.get_case("llm_factual_basic")
        llm_res = evaluate_llm_deterministic(llm_case, "Paris")

        rag_case = DEFAULT_GOLDEN_DATASET.get_case("rag_answerable_token")
        rag_res = evaluate_rag_pipeline_case(
            rag_case,
            retrieved_chunks=[{"source": "llm-basics.md", "content": "A token is a unit of text."}],
            answer="A token is a unit of text.",
            cited_sources=["llm-basics.md"],
        )

        auto_case = DEFAULT_GOLDEN_DATASET.get_case("auto_calculator_basic")
        task = TaskPlan(
            description="Calc",
            steps=[TaskStep(1, "calculator", {"expression": "10+20"}, StepStatus.COMPLETED, 30)],
            status=TaskStatus.COMPLETED,
        )
        traj_res = evaluate_trajectory(auto_case, task)

        result = runner.compile_run(
            llm_results=[llm_res],
            rag_results=[rag_res],
            trajectory_results=[traj_res],
        )
        self.assertEqual(result.overall_status, "PASS")

        report = runner.format_report(result)
        self.assertIn("AI ENGINEERING EVALUATION", report)
        self.assertIn("Mode: deterministic", report)
        self.assertIn("Correctness: 1.00", report)
        self.assertIn("Recovery: N/A", report)  # Not fabricated when not evaluated
        self.assertIn("NOT RUN", report)  # Regression not run
        self.assertIn("Overall: PASS", report)

    def test_security_golden_cases_evaluated_deterministically(self):
        runner = EvaluationRunner(
            dataset=DEFAULT_GOLDEN_DATASET,
            evaluation_mode="deterministic",
        )
        traj_results = []
        for sec_case in SECURITY_GOLDEN_CASES:
            # Blocked task (status FAILED) matches expected_success=False
            blocked_task = TaskPlan(
                description="Blocked security request",
                steps=[TaskStep(1, "blocked", {}, StepStatus.FAILED, error="Rejected")],
                status=TaskStatus.FAILED,
            )
            traj_results.append(evaluate_trajectory(sec_case, blocked_task))

        result = runner.compile_run(trajectory_results=traj_results)
        self.assertEqual(result.overall_status, "PASS")
        self.assertEqual(result.aggregate_metrics()["agent_execution"], 1.0)


if __name__ == "__main__":
    unittest.main()
