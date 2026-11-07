import unittest

from src.automation.models import TaskPlan, TaskStep
from src.automation.tool_setup import create_tool_registry
from src.automation.validator import TaskValidator


class TestTaskValidator(unittest.TestCase):
    def setUp(self):
        self.registry = create_tool_registry()
        self.validator = TaskValidator(self.registry)

    def test_valid_plan(self):
        task = TaskPlan(
            description="List documents",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="list_files",
                    arguments={},
                )
            ],
        )

        self.assertTrue(self.validator.validate(task))

    def test_unknown_tool_rejected(self):
        task = TaskPlan(
            description="Unknown tool",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="delete_everything",
                    arguments={},
                )
            ],
        )

        with self.assertRaises(ValueError):
            self.validator.validate(task)

    def test_missing_argument_rejected(self):
        task = TaskPlan(
            description="Read file",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="read_file",
                    arguments={},
                )
            ],
        )

        with self.assertRaises(ValueError):
            self.validator.validate(task)

    def test_future_reference_rejected(self):
        task = TaskPlan(
            description="Invalid reference",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="summarize_text",
                    arguments={"text": "$step_2"},
                ),
                TaskStep(
                    step_id=2,
                    tool="read_file",
                    arguments={"path": "documents/ai-engineering.md"},
                ),
            ],
        )

        with self.assertRaises(ValueError):
            self.validator.validate(task)

    def test_non_sequential_step_ids_rejected(self):
        with self.assertRaises(ValueError):
            TaskPlan(
                description="Invalid step IDs",
                steps=[
                    TaskStep(
                        step_id=1,
                        tool="list_files",
                        arguments={},
                    ),
                    TaskStep(
                        step_id=3,
                        tool="list_files",
                        arguments={},
                    ),
                ],
            )

    def test_nonexistent_step_reference_rejected(self):
        plan = TaskPlan(
            description="Invalid reference",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="list_files",
                    arguments={},
                ),
                TaskStep(
                    step_id=2,
                    tool="summarize_text",
                    arguments={
                        "text": "$step_99",
                    },
                ),
            ],
        )

        with self.assertRaises(ValueError):
            self.validator.validate(plan)

    def test_previous_step_reference_accepted(self):
        plan = TaskPlan(
            description="Valid reference",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="list_files",
                    arguments={},
                ),
                TaskStep(
                    step_id=2,
                    tool="summarize_text",
                    arguments={
                        "text": "$step_1",
                    },
                ),
            ],
        )

        self.assertTrue(self.validator.validate(plan))

    def test_more_than_five_steps_rejected(self):
        steps = [
            TaskStep(
                step_id=i,
                tool="list_files",
                arguments={},
            )
            for i in range(1, 7)
        ]

        with self.assertRaises(ValueError):
            TaskPlan(
                description="Too many steps",
                steps=steps,
            )


if __name__ == "__main__":
    unittest.main()