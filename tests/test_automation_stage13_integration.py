import tempfile
import unittest
from pathlib import Path

from src.automation.config import AutomationConfig
from src.automation.evaluation import (
    EvaluationMetrics,
    RegressionEvaluator,
    generate_evaluation_report,
    run_regression_evaluation,
)
from src.automation.evaluation_cases import EVALUATION_CASES, REFERENCE_PLANS
from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger
from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestStage13IntegrationWithHardenedArchitecture(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.config = AutomationConfig(db_path=self.db_path)
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="calculator",
                description="Calculator tool",
                handler=lambda expression: 30,
                required_arguments={"expression"},
            )
        )
        self.task_store = TaskStore(config=self.config)
        self.logger = TaskLogger(config=self.config)
        self.executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
            config=self.config,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stage13_regression_evaluator_passes_with_reference_plans(self):
        evaluator = RegressionEvaluator(
            cases=EVALUATION_CASES,
            reference_plans=REFERENCE_PLANS,
        )
        summary = evaluator.evaluate(strict=True)
        self.assertEqual(summary.total_cases, 5)
        self.assertEqual(summary.planning_accuracy, 1.0)
        self.assertEqual(summary.tool_selection_accuracy, 1.0)
        self.assertEqual(summary.execution_outcome_accuracy, 1.0)

    def test_stage13_run_regression_and_report_generation(self):
        summary, summary_text = run_regression_evaluation(strict=True)
        report = generate_evaluation_report(
            summary=summary,
            recovery_success=1.0,
            trace_completeness=1.0,
            approval_compliance=1.0,
        )
        self.assertIn("Stage 13 Evaluation Report", report)
        self.assertIn("Planning accuracy: 1.00", report)
        self.assertIn("Tool selection accuracy: 1.00", report)
        self.assertIn("Execution outcome accuracy: 1.00", report)

    def test_stage13_metrics_from_hardened_task_run(self):
        task = TaskPlan(
            description="Hitung 10 + 20",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="calculator",
                    arguments={"expression": "10 + 20"},
                )
            ],
        )
        result = self.executor.execute(task)
        logs = self.logger.get_task_logs(task.task_id)

        metrics = EvaluationMetrics.from_task(
            task=result,
            plan_valid=True,
            logs=logs,
            registry=self.registry,
        )

        self.assertTrue(metrics.plan_valid)
        self.assertTrue(metrics.task_success)
        self.assertEqual(metrics.step_success_rate, 1.0)
        self.assertTrue(metrics.approval_compliance)
        self.assertTrue(metrics.trace_complete)


if __name__ == "__main__":
    unittest.main()
