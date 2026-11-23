import unittest

from src.automation.evaluation import EvaluationMetrics
from src.automation.models import (
    StepStatus,
    TaskPlan,
    TaskStatus,
    TaskStep,
)

class TestEvaluationMetrics(unittest.TestCase):
    def test_successful_task_metrics(self):
        metrics = EvaluationMetrics(
            plan_valid=True,
            task_success=True,
            step_success_rate=1.0,
            approval_compliance=True,
            recovery_success=None,
            trace_complete=True,
        )

        self.assertTrue(metrics.plan_valid)
        self.assertTrue(metrics.task_success)
        self.assertEqual(metrics.step_success_rate, 1.0)
        self.assertTrue(metrics.approval_compliance)
        self.assertIsNone(metrics.recovery_success)
        self.assertTrue(metrics.trace_complete)

    def test_failed_task_metrics(self):
        metrics = EvaluationMetrics(
            plan_valid=True,
            task_success=False,
            step_success_rate=0.5,
            approval_compliance=True,
            recovery_success=False,
            trace_complete=True,
        )

        self.assertTrue(metrics.plan_valid)
        self.assertFalse(metrics.task_success)
        self.assertEqual(metrics.step_success_rate, 0.5)
        self.assertTrue(metrics.approval_compliance)
        self.assertFalse(metrics.recovery_success)
        self.assertTrue(metrics.trace_complete)

    def test_invalid_step_success_rate_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationMetrics(
                plan_valid=True,
                task_success=True,
                step_success_rate=1.5,
                approval_compliance=True,
                recovery_success=None,
                trace_complete=True,
            )

    def test_evaluate_completed_task(self):
        task = TaskPlan(
            description="Evaluate completed task",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="first",
                    status=StepStatus.COMPLETED,
                ),
                TaskStep(
                    step_id=2,
                    tool="second",
                    status=StepStatus.COMPLETED,
                ),
            ],
            status=TaskStatus.COMPLETED,
        )

        metrics = EvaluationMetrics.from_task(
            task,
            plan_valid=True,
        )

        self.assertTrue(metrics.plan_valid)
        self.assertTrue(metrics.task_success)
        self.assertEqual(metrics.step_success_rate, 1.0)

    def test_evaluate_partially_failed_task(self):
        task = TaskPlan(
            description="Evaluate failed task",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="first",
                    status=StepStatus.COMPLETED,
                ),
                TaskStep(
                    step_id=2,
                    tool="second",
                    status=StepStatus.FAILED,
                ),
            ],
            status=TaskStatus.FAILED,
        )

        metrics = EvaluationMetrics.from_task(
            task,
            plan_valid=True,
        )

        self.assertTrue(metrics.plan_valid)
        self.assertFalse(metrics.task_success)
        self.assertEqual(metrics.step_success_rate, 0.5)

    def test_task_metrics_without_execution_evidence_are_unknown(self):
        task = TaskPlan(
            description="Evaluate task without execution evidence",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="first",
                    status=StepStatus.COMPLETED,
                ),
            ],
            status=TaskStatus.COMPLETED,
        )

        metrics = EvaluationMetrics.from_task(
            task,
            plan_valid=True,
        )

        self.assertIsNone(metrics.approval_compliance)
        self.assertIsNone(metrics.recovery_success)
        self.assertIsNone(metrics.trace_complete)


if __name__ == "__main__":
    unittest.main()