import unittest

from src.automation.evaluation import (
    RunMetrics,
    collect_run_metrics,
)
from src.automation.models import TaskPlan, TaskStatus, TaskStep, StepStatus


class TestStructuredRunMetrics(unittest.TestCase):
    def test_successful_run_metrics(self):
        task = TaskPlan(
            task_id="task_success",
            description="Run successful task",
            steps=[
                TaskStep(step_id=1, tool="t1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="t2", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        logs = [
            {"task_id": "task_success", "event": "task_started", "created_at": "2026-11-23T10:00:00+00:00"},
            {"task_id": "task_success", "step_id": 1, "event": "step_started", "created_at": "2026-11-23T10:00:01+00:00"},
            {"task_id": "task_success", "step_id": 1, "event": "step_completed", "created_at": "2026-11-23T10:00:02+00:00"},
            {"task_id": "task_success", "step_id": 2, "event": "step_started", "created_at": "2026-11-23T10:00:03+00:00"},
            {"task_id": "task_success", "step_id": 2, "event": "step_completed", "created_at": "2026-11-23T10:00:04+00:00"},
            {"task_id": "task_success", "event": "task_completed", "created_at": "2026-11-23T10:00:05+00:00"},
        ]

        metrics = collect_run_metrics(task, logs)

        self.assertEqual(metrics.run_id, "task_success")
        self.assertEqual(metrics.task_id, "task_success")
        self.assertEqual(metrics.task_status, TaskStatus.COMPLETED)
        self.assertEqual(metrics.step_count, 2)
        self.assertEqual(metrics.completed_steps, 2)
        self.assertEqual(metrics.failed_steps, 0)
        self.assertEqual(metrics.approval_requests, 0)
        self.assertEqual(metrics.approval_denials, 0)
        self.assertEqual(metrics.duration_seconds, 5.0)

    def test_failed_run_metrics(self):
        task = TaskPlan(
            task_id="task_fail",
            description="Run failed task",
            steps=[
                TaskStep(step_id=1, tool="t1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="t2", status=StepStatus.FAILED),
            ],
            status=TaskStatus.FAILED,
        )
        logs = [
            {"task_id": "task_fail", "event": "task_started", "created_at": "2026-11-23T10:00:00+00:00"},
            {"task_id": "task_fail", "step_id": 2, "event": "step_failed", "created_at": "2026-11-23T10:00:02+00:00"},
            {"task_id": "task_fail", "event": "task_failed", "created_at": "2026-11-23T10:00:03+00:00"},
        ]

        metrics = collect_run_metrics(task, logs)

        self.assertEqual(metrics.task_status, TaskStatus.FAILED)
        self.assertEqual(metrics.step_count, 2)
        self.assertEqual(metrics.completed_steps, 1)
        self.assertEqual(metrics.failed_steps, 1)
        self.assertEqual(metrics.duration_seconds, 3.0)

    def test_approval_flow_run_metrics(self):
        task = TaskPlan(
            task_id="task_approval",
            description="Run approval task",
            steps=[
                TaskStep(step_id=1, tool="dangerous", status=StepStatus.FAILED),
            ],
            status=TaskStatus.FAILED,
        )
        logs = [
            {"task_id": "task_approval", "event": "task_started", "created_at": "2026-11-23T10:00:00+00:00"},
            {"task_id": "task_approval", "step_id": 1, "event": "approval_requested", "created_at": "2026-11-23T10:00:01+00:00"},
            {"task_id": "task_approval", "step_id": 1, "event": "approval_denied", "created_at": "2026-11-23T10:00:02+00:00"},
            {"task_id": "task_approval", "event": "task_failed", "created_at": "2026-11-23T10:00:03+00:00"},
        ]

        metrics = collect_run_metrics(task, logs)

        self.assertEqual(metrics.approval_requests, 1)
        self.assertEqual(metrics.approval_denials, 1)

    def test_partial_execution_and_missing_optional_evidence(self):
        task = TaskPlan(
            task_id="task_partial",
            description="Partially executed task",
            steps=[
                TaskStep(step_id=1, tool="t1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="t2", status=StepStatus.PENDING),
            ],
            status=TaskStatus.RUNNING,
        )

        metrics = collect_run_metrics(task, logs=None)

        self.assertEqual(metrics.task_status, TaskStatus.RUNNING)
        self.assertEqual(metrics.completed_steps, 1)
        self.assertEqual(metrics.failed_steps, 0)
        self.assertEqual(metrics.approval_requests, 0)
        self.assertEqual(metrics.approval_denials, 0)
        self.assertIsNone(metrics.duration_seconds)

    def test_invalid_task_type_rejected(self):
        with self.assertRaises(TypeError):
            collect_run_metrics("not_a_task")

    def test_dataclass_validation(self):
        with self.assertRaises(ValueError):
            RunMetrics(
                run_id="",
                task_id="t1",
                task_status=TaskStatus.COMPLETED,
                step_count=1,
                completed_steps=1,
                failed_steps=0,
                approval_requests=0,
                approval_denials=0,
            )

        with self.assertRaises(ValueError):
            RunMetrics(
                run_id="r1",
                task_id="t1",
                task_status=TaskStatus.COMPLETED,
                step_count=-1,
                completed_steps=0,
                failed_steps=0,
                approval_requests=0,
                approval_denials=0,
            )

        with self.assertRaises(ValueError):
            RunMetrics(
                run_id="r1",
                task_id="t1",
                task_status=TaskStatus.COMPLETED,
                step_count=1,
                completed_steps=1,
                failed_steps=0,
                approval_requests=0,
                approval_denials=0,
                duration_seconds=-2.0,
            )


if __name__ == "__main__":
    unittest.main()
