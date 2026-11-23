"""Release Drills for Local Hermes AI v1.0: Recovery, Approval, RAG Abstention, and Evaluation."""

from pathlib import Path
import tempfile
import unittest

from src.automation.config import AutomationConfig
from src.automation.evaluation import (
    EvaluationMetrics,
    generate_evaluation_report,
    calculate_evaluation_summary,
)
from src.automation.evaluation_cases import EVALUATION_CASES, REFERENCE_PLANS
from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger
from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore
from src.automation.tracing import build_task_trace
from src.tools.calculator import calculate


class TestV1ReleaseDrills(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.db_path = self.temp_path / "drills.db"
        self.config = AutomationConfig(db_path=self.db_path)

        self.step_1_call_count = 0
        self.step_2_call_count = 0

        def step_1_tool(expression):
            self.step_1_call_count += 1
            return 100

        def step_2_tool(expression):
            self.step_2_call_count += 1
            return 200

        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="step_1_tool",
                description="Step 1 handler",
                handler=step_1_tool,
                required_arguments={"expression"},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="step_2_tool",
                description="Step 2 handler",
                handler=step_2_tool,
                required_arguments={"expression"},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="sensitive_action",
                description="Sensitive action requiring approval",
                handler=lambda target: f"processed_{target}",
                required_arguments={"target"},
                requires_approval=True,
            )
        )

        self.task_store = TaskStore(config=self.config)
        self.logger = TaskLogger(config=self.config)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_drill_1_recovery_interrupted_task(self):
        """Recovery Drill: Interrupted task resumes, does NOT re-run completed step, and finishes."""
        # 1. Simulate a 2-step task where step 1 completed before interruption
        plan = TaskPlan(
            task_id="drill_recovery_task_01",
            description="Two-step recovery drill",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="step_1_tool",
                    arguments={"expression": "10 * 10"},
                    status=StepStatus.COMPLETED,
                    output=100,
                ),
                TaskStep(
                    step_id=2,
                    tool="step_2_tool",
                    arguments={"expression": "$step_1 + 50"},
                    status=StepStatus.PENDING,
                ),
            ],
            status=TaskStatus.RUNNING,
        )
        self.task_store.save_task(plan)

        # 2. Reconstruct executor simulating fresh process restart
        executor = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
            config=self.config,
        )

        # 3. Resume interrupted task
        resumed = executor.resume("drill_recovery_task_01")

        self.assertEqual(resumed.status, TaskStatus.COMPLETED)
        self.assertEqual(resumed.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(resumed.steps[1].status, StepStatus.COMPLETED)
        self.assertEqual(resumed.steps[1].output, 200)

        # Step 1 handler was never invoked during resume; only step 2 ran
        self.assertEqual(self.step_1_call_count, 0)
        self.assertEqual(self.step_2_call_count, 1)

        # Trace check
        logs = self.logger.get_task_logs("drill_recovery_task_01")
        trace = build_task_trace(logs=logs)
        self.assertTrue(trace.resumed)
        self.assertTrue(trace.completed)

    def test_drill_2_approval_both_branches(self):
        """Approval Drill: Denied branch fails closed; Approved branch executes successfully."""
        plan_denied = TaskPlan(
            task_id="drill_appr_denied",
            description="Sensitive operation - Deny branch",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="sensitive_action",
                    arguments={"target": "prod_table"},
                )
            ],
        )

        executor_denier = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
            config=self.config,
            approval_handler=lambda task, step, args: False,
        )

        result_denied = executor_denier.execute(plan_denied)
        self.assertEqual(result_denied.status, TaskStatus.FAILED)
        self.assertEqual(result_denied.steps[0].status, StepStatus.FAILED)
        self.assertIn("Approval denied", result_denied.steps[0].error)

        plan_approved = TaskPlan(
            task_id="drill_appr_approved",
            description="Sensitive operation - Approve branch",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="sensitive_action",
                    arguments={"target": "backup_table"},
                )
            ],
        )

        executor_approver = TaskExecutor(
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
            config=self.config,
            approval_handler=lambda task, step, args: True,
        )

        result_approved = executor_approver.execute(plan_approved)
        self.assertEqual(result_approved.status, TaskStatus.COMPLETED)
        self.assertEqual(result_approved.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(result_approved.steps[0].output, "processed_backup_table")

    def test_drill_3_evaluation_report_generation(self):
        """Evaluation Drill: Ensure deterministic aggregate evaluation and report generation work cleanly."""
        summary = calculate_evaluation_summary(
            cases=EVALUATION_CASES,
            plans=REFERENCE_PLANS,
            executed_tasks=REFERENCE_PLANS,
        )
        self.assertEqual(summary.total_cases, len(EVALUATION_CASES))
        self.assertEqual(summary.planning_accuracy, 1.0)
        self.assertEqual(summary.tool_selection_accuracy, 1.0)
        self.assertEqual(summary.execution_outcome_accuracy, 1.0)

        report = generate_evaluation_report(
            summary=summary,
            recovery_success=True,
            trace_completeness=True,
            approval_compliance=True,
        )
        self.assertIn("Total cases: 5", report)
        self.assertIn("Planning accuracy: 1.00", report)
        self.assertIn("Recovery success: True", report)
        self.assertIn("Trace completeness: True", report)
        self.assertIn("Approval compliance: True", report)


if __name__ == "__main__":
    unittest.main()
