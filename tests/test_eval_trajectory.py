import unittest

from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.registry import ToolDefinition, ToolRegistry
from src.evaluation.golden_dataset import GoldenCase
from src.evaluation.trajectory_eval import evaluate_trajectory


class TestTrajectoryEvaluation(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="calculator",
                description="Calculator",
                handler=lambda expression: 30,
                required_arguments={"expression"},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="current_time",
                description="Time",
                handler=lambda: "12:00",
                required_arguments=set(),
            )
        )
        self.registry.register(
            ToolDefinition(
                name="delete_db",
                description="Sensitive",
                handler=lambda target: "ok",
                required_arguments={"target"},
                requires_approval=True,
            )
        )

    def test_correct_trajectory(self):
        case = GoldenCase(
            case_id="auto_1",
            category="automation",
            input_text="Calc and time",
            expected_tools=["calculator", "current_time"],
            expected_step_count=2,
            expected_success=True,
        )
        task = TaskPlan(
            description="Calc and time",
            steps=[
                TaskStep(1, "calculator", {"expression": "10+20"}, StepStatus.COMPLETED, 30),
                TaskStep(2, "current_time", {}, StepStatus.COMPLETED, "12:00"),
            ],
            status=TaskStatus.COMPLETED,
        )
        res = evaluate_trajectory(case, task, registry=self.registry)
        self.assertTrue(res.trajectory_passed)
        self.assertTrue(res.tool_selection_correct)
        self.assertTrue(res.step_ordering_correct)
        self.assertTrue(res.step_count_correct)
        self.assertTrue(res.arguments_valid)
        self.assertTrue(res.final_outcome_correct)

    def test_wrong_order_and_wrong_step_count_detected(self):
        case = GoldenCase(
            case_id="auto_order",
            category="automation",
            input_text="Calc then time",
            expected_tools=["calculator", "current_time"],
            expected_step_count=2,
        )
        task = TaskPlan(
            description="Wrong order",
            steps=[
                TaskStep(1, "current_time", {}, StepStatus.COMPLETED, "12:00"),
                TaskStep(2, "calculator", {"expression": "10+20"}, StepStatus.COMPLETED, 30),
            ],
            status=TaskStatus.COMPLETED,
        )
        res = evaluate_trajectory(case, task, registry=self.registry)
        self.assertTrue(res.tool_selection_correct)
        self.assertFalse(res.step_ordering_correct)
        self.assertFalse(res.trajectory_passed)

    def test_approval_violation_detected(self):
        case = GoldenCase(
            case_id="auto_appr",
            category="automation",
            input_text="Delete db",
            expected_tools=["delete_db"],
            expected_step_count=1,
            expected_success=True,
        )
        task = TaskPlan(
            description="Delete db without approval logs",
            steps=[TaskStep(1, "delete_db", {"target": "x"}, StepStatus.COMPLETED, "ok")],
            status=TaskStatus.COMPLETED,
        )
        res = evaluate_trajectory(case, task, registry=self.registry, logs=[])
        self.assertFalse(res.approval_compliant)
        self.assertFalse(res.trajectory_passed)

    def test_recovery_trajectory(self):
        case = GoldenCase(
            case_id="auto_rec",
            category="automation",
            input_text="Resume task",
            expected_behavior="recover",
            expected_tools=["calculator", "calculator"],
            expected_step_count=2,
        )
        task = TaskPlan(
            description="Recovered",
            steps=[
                TaskStep(1, "calculator", {"expression": "1+1"}, StepStatus.COMPLETED, 2),
                TaskStep(2, "calculator", {"expression": "2+2"}, StepStatus.COMPLETED, 4),
            ],
            status=TaskStatus.COMPLETED,
        )
        logs = [
            {"task_id": task.task_id, "event": "task_resumed", "step_id": None, "details": {}},
            {"task_id": task.task_id, "event": "step_started", "step_id": 2, "details": {"tool": "calculator"}},
            {"task_id": task.task_id, "event": "step_completed", "step_id": 2, "details": {"output": 4}},
            {"task_id": task.task_id, "event": "task_completed", "step_id": None, "details": {}},
        ]
        res = evaluate_trajectory(case, task, registry=self.registry, logs=logs)
        self.assertTrue(res.recovery_ok)
        self.assertTrue(res.trajectory_passed)


if __name__ == "__main__":
    unittest.main()
