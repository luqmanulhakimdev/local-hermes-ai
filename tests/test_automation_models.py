
import unittest

from src.automation.models import (
    TaskPlan,
    TaskStep,
    TaskStatus,
    StepStatus,
)


class TestAutomationModels(unittest.TestCase):

    def test_create_task_plan(self):
        step = TaskStep(
            step_id=1,
            tool="read_file",
            arguments={"path": "documents/ai-engineering.md"},
        )

        task = TaskPlan(
            description="Read an AI document",
            steps=[step],
        )

        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(step.status, StepStatus.PENDING)
        self.assertTrue(task.task_id)

    def test_empty_description_is_rejected(self):
        with self.assertRaises(ValueError):
            TaskPlan(description="", steps=[
                TaskStep(step_id=1, tool="read_file")
            ])

    def test_empty_steps_are_rejected(self):
        with self.assertRaises(ValueError):
            TaskPlan(description="Test task", steps=[])

    def test_more_than_five_steps_are_rejected(self):
        steps = [
            TaskStep(step_id=i, tool="test_tool")
            for i in range(1, 7)
        ]

        with self.assertRaisesRegex(ValueError, "more than 5"):
            TaskPlan(description="Too many steps", steps=steps)

    def test_duplicate_step_ids_are_rejected(self):
        steps = [
            TaskStep(step_id=1, tool="read_file"),
            TaskStep(step_id=1, tool="save_note"),
        ]

        with self.assertRaisesRegex(ValueError, "unique"):
            TaskPlan(description="Duplicate IDs", steps=steps)


if __name__ == "__main__":
    unittest.main()
