import unittest

from src.automation.evaluation import RAGEvaluationMetrics, evaluate_rag_case
from src.automation.evaluation_cases import RAG_EVALUATION_CASES, RAG_REFERENCE_PLANS
from src.automation.models import TaskPlan, TaskStep
from src.automation.rag_context import ContextChunk, RetrievedContext
from src.automation.registry import ToolDefinition, ToolRegistry


class TestRAGAutomationEvaluation(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="calculator",
                description="Calculator tool",
                handler=lambda expression: 303 * 2,
                required_arguments={"expression"},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="list_files",
                description="List files",
                handler=lambda directory="documents": [],
                required_arguments=set(),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="read_file",
                description="Read file",
                handler=lambda path: "content",
                required_arguments={"path"},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="summarize_text",
                description="Summarize text",
                handler=lambda text: "summary",
                required_arguments={"text"},
            )
        )

    def test_rag_cases_dataset_integrity(self):
        self.assertGreaterEqual(len(RAG_EVALUATION_CASES), 4)
        case_ids = [c.case_id for c in RAG_EVALUATION_CASES]
        self.assertEqual(len(case_ids), len(set(case_ids)))

        for case in RAG_EVALUATION_CASES:
            self.assertIn(case.case_id, RAG_REFERENCE_PLANS)
            ref_plan = RAG_REFERENCE_PLANS[case.case_id]
            self.assertEqual(len(ref_plan.steps), case.expected_step_count)
            self.assertEqual([s.tool for s in ref_plan.steps], case.expected_tools)

    def test_rag_evaluation_metrics_validation(self):
        with self.assertRaises(ValueError):
            RAGEvaluationMetrics(
                case_id="",
                plan_valid=True,
                expected_tools_matched=True,
                context_used=True,
                safety_preserved=True,
                step_count_matched=True,
            )

    def test_evaluate_rag_case_success(self):
        case = RAG_EVALUATION_CASES[0]  # rag_calculator_basic
        plan = RAG_REFERENCE_PLANS[case.case_id]
        chunk = ContextChunk(content="303 * 2", source="doc.md", score=0.9)
        context = RetrievedContext(query="calc", chunks=[chunk])

        metrics = evaluate_rag_case(case, plan, context=context, registry=self.registry)
        self.assertEqual(metrics.case_id, case.case_id)
        self.assertTrue(metrics.plan_valid)
        self.assertTrue(metrics.expected_tools_matched)
        self.assertTrue(metrics.context_used)
        self.assertTrue(metrics.safety_preserved)
        self.assertTrue(metrics.step_count_matched)

    def test_evaluate_rag_case_safety_violation(self):
        case = RAG_EVALUATION_CASES[0]
        # Plan with invalid tool not in registry
        unsafe_plan = TaskPlan(
            description="Unsafe plan",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="forbidden_shell",
                    arguments={},
                )
            ],
        )
        metrics = evaluate_rag_case(case, unsafe_plan, registry=self.registry)
        self.assertFalse(metrics.plan_valid)
        self.assertFalse(metrics.safety_preserved)
        self.assertFalse(metrics.expected_tools_matched)


if __name__ == "__main__":
    unittest.main()
