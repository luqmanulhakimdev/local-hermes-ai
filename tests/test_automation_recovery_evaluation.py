import unittest

from src.automation.evaluation import evaluate_recovery_success
from src.automation.models import TaskPlan, TaskStatus, TaskStep, StepStatus


class TestRecoveryEvaluation(unittest.TestCase):
    def test_successful_recovery_with_task(self):
        task = TaskPlan(
            task_id="t1",
            description="Recovered task",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        logs = [
            {"event": "task_started", "task_id": "t1"},
            {"event": "task_resumed", "task_id": "t1", "message": "Resumed from step 2"},
            {"event": "step_started", "task_id": "t1", "step_id": 2},
            {"event": "step_completed", "task_id": "t1", "step_id": 2},
            {"event": "task_completed", "task_id": "t1"},
        ]
        result = evaluate_recovery_success(task=task, logs=logs)
        self.assertTrue(result)

    def test_failed_recovery_with_task(self):
        task = TaskPlan(
            task_id="t2",
            description="Failed recovery task",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.FAILED),
            ],
            status=TaskStatus.FAILED,
        )
        logs = [
            {"event": "task_started", "task_id": "t2"},
            {"event": "task_resumed", "task_id": "t2"},
            {"event": "step_started", "task_id": "t2", "step_id": 2},
            {"event": "step_failed", "task_id": "t2", "step_id": 2},
            {"event": "task_failed", "task_id": "t2"},
        ]
        result = evaluate_recovery_success(task=task, logs=logs)
        self.assertFalse(result)

    def test_successful_recovery_from_logs_only(self):
        logs = [
            {"event": "task_started", "task_id": "t3"},
            {"event": "task_resumed", "task_id": "t3"},
            {"event": "task_completed", "task_id": "t3"},
        ]
        result = evaluate_recovery_success(task=None, logs=logs)
        self.assertTrue(result)

    def test_failed_recovery_from_logs_only(self):
        logs = [
            {"event": "task_started", "task_id": "t4"},
            {"event": "task_resumed", "task_id": "t4"},
            {"event": "task_failed", "task_id": "t4"},
        ]
        result = evaluate_recovery_success(task=None, logs=logs)
        self.assertFalse(result)

    def test_no_resume_event_returns_none(self):
        task = TaskPlan(
            task_id="t5",
            description="Normal task",
            steps=[TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED)],
            status=TaskStatus.COMPLETED,
        )
        logs = [
            {"event": "task_started", "task_id": "t5"},
            {"event": "step_started", "task_id": "t5", "step_id": 1},
            {"event": "step_completed", "task_id": "t5", "step_id": 1},
            {"event": "task_completed", "task_id": "t5"},
        ]
        result = evaluate_recovery_success(task=task, logs=logs)
        self.assertIsNone(result)

    def test_missing_logs_returns_none(self):
        task = TaskPlan(
            task_id="t6",
            description="Task without logs",
            steps=[TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED)],
            status=TaskStatus.COMPLETED,
        )
        self.assertIsNone(evaluate_recovery_success(task=task, logs=None))
        self.assertIsNone(evaluate_recovery_success(task=None, logs=None))

    def test_invalid_types_raise_error(self):
        with self.assertRaises(TypeError):
            evaluate_recovery_success(task="invalid", logs=[])
        with self.assertRaises(TypeError):
            evaluate_recovery_success(task=None, logs="not_a_list")


if __name__ == "__main__":
    unittest.main()
