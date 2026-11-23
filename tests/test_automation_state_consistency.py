import unittest

from src.automation.models import (
    StepStatus,
    TaskPlan,
    TaskStatus,
    TaskStep,
    validate_task_state_consistency,
)


class TestStateConsistency(unittest.TestCase):
    def test_valid_completed_task(self):
        task = TaskPlan(
            description="Valid completed task",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        validate_task_state_consistency(task)

    def test_valid_failed_task(self):
        task = TaskPlan(
            description="Valid failed task",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.FAILED),
            ],
            status=TaskStatus.FAILED,
        )
        validate_task_state_consistency(task)

    def test_valid_awaiting_approval_task(self):
        task = TaskPlan(
            description="Valid awaiting approval",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.AWAITING_APPROVAL),
            ],
            status=TaskStatus.AWAITING_APPROVAL,
        )
        validate_task_state_consistency(task)

    def test_valid_cancelled_task(self):
        task = TaskPlan(
            description="Valid cancelled task",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.PENDING),
            ],
            status=TaskStatus.CANCELLED,
        )
        validate_task_state_consistency(task)

    def test_completed_task_with_pending_step_rejected(self):
        task = TaskPlan(
            description="Invalid completed task",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.PENDING),
            ],
            status=TaskStatus.COMPLETED,
        )
        with self.assertRaises(ValueError):
            validate_task_state_consistency(task)

    def test_completed_task_with_failed_step_rejected(self):
        task = TaskPlan(
            description="Invalid completed task with failed step",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.FAILED),
            ],
            status=TaskStatus.COMPLETED,
        )
        with self.assertRaises(ValueError):
            validate_task_state_consistency(task)

    def test_failed_task_without_failed_step_rejected(self):
        task = TaskPlan(
            description="Failed task without failed step",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.FAILED,
        )
        with self.assertRaises(ValueError):
            validate_task_state_consistency(task)

    def test_failed_task_with_running_step_rejected(self):
        task = TaskPlan(
            description="Failed task with running step",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.FAILED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.RUNNING),
            ],
            status=TaskStatus.FAILED,
        )
        with self.assertRaises(ValueError):
            validate_task_state_consistency(task)

    def test_awaiting_approval_task_without_approval_step_rejected(self):
        task = TaskPlan(
            description="Awaiting approval without step",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.PENDING),
            ],
            status=TaskStatus.AWAITING_APPROVAL,
        )
        with self.assertRaises(ValueError):
            validate_task_state_consistency(task)

    def test_cancelled_task_with_running_step_rejected(self):
        task = TaskPlan(
            description="Cancelled task with running step",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.RUNNING),
            ],
            status=TaskStatus.CANCELLED,
        )
        with self.assertRaises(ValueError):
            validate_task_state_consistency(task)


if __name__ == "__main__":
    unittest.main()
