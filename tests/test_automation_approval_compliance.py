import unittest

from src.automation.evaluation import evaluate_approval_compliance
from src.automation.models import TaskPlan, TaskStatus, TaskStep, StepStatus
from src.automation.registry import ToolDefinition, ToolRegistry


class TestApprovalComplianceEvaluation(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="safe_tool",
                description="Safe tool",
                handler=lambda: "ok",
                required_arguments=set(),
                requires_approval=False,
            )
        )
        self.registry.register(
            ToolDefinition(
                name="sensitive_tool",
                description="Sensitive tool",
                handler=lambda: "ok",
                required_arguments=set(),
                requires_approval=True,
            )
        )

    def test_safe_tools_only_is_compliant(self):
        task = TaskPlan(
            task_id="t1",
            description="Safe task",
            steps=[
                TaskStep(step_id=1, tool="safe_tool", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        result = evaluate_approval_compliance(task, registry=self.registry, logs=None)
        self.assertTrue(result)

    def test_sensitive_tool_without_logs_returns_none(self):
        task = TaskPlan(
            task_id="t2",
            description="Sensitive task",
            steps=[
                TaskStep(step_id=1, tool="sensitive_tool", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        result = evaluate_approval_compliance(task, registry=self.registry, logs=None)
        self.assertIsNone(result)

    def test_sensitive_tool_approved_returns_true(self):
        task = TaskPlan(
            task_id="t3",
            description="Sensitive task",
            steps=[
                TaskStep(step_id=1, tool="sensitive_tool", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        logs = [
            {"event": "task_started", "task_id": "t3"},
            {"event": "step_started", "task_id": "t3", "step_id": 1},
            {"event": "approval_requested", "task_id": "t3", "step_id": 1, "details": {"tool": "sensitive_tool"}},
            {"event": "approval_granted", "task_id": "t3", "step_id": 1, "details": {"tool": "sensitive_tool"}},
            {"event": "step_completed", "task_id": "t3", "step_id": 1},
            {"event": "task_completed", "task_id": "t3"},
        ]
        result = evaluate_approval_compliance(task, registry=self.registry, logs=logs)
        self.assertTrue(result)

    def test_sensitive_tool_denied_returns_false(self):
        task = TaskPlan(
            task_id="t4",
            description="Sensitive task denied",
            steps=[
                TaskStep(step_id=1, tool="sensitive_tool", status=StepStatus.FAILED),
            ],
            status=TaskStatus.FAILED,
        )
        logs = [
            {"event": "task_started", "task_id": "t4"},
            {"event": "step_started", "task_id": "t4", "step_id": 1},
            {"event": "approval_requested", "task_id": "t4", "step_id": 1, "details": {"tool": "sensitive_tool"}},
            {"event": "approval_denied", "task_id": "t4", "step_id": 1, "details": {"tool": "sensitive_tool"}},
            {"event": "task_failed", "task_id": "t4"},
        ]
        result = evaluate_approval_compliance(task, registry=self.registry, logs=logs)
        self.assertFalse(result)

    def test_sensitive_tool_executed_without_approval_returns_false(self):
        task = TaskPlan(
            task_id="t5",
            description="Unapproved execution",
            steps=[
                TaskStep(step_id=1, tool="sensitive_tool", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        logs = [
            {"event": "task_started", "task_id": "t5"},
            {"event": "step_started", "task_id": "t5", "step_id": 1},
            {"event": "step_completed", "task_id": "t5", "step_id": 1},
            {"event": "task_completed", "task_id": "t5"},
        ]
        result = evaluate_approval_compliance(task, registry=self.registry, logs=logs)
        self.assertFalse(result)

    def test_invalid_types_raise_error(self):
        with self.assertRaises(TypeError):
            evaluate_approval_compliance("not_a_task")
        task = TaskPlan(
            task_id="t6",
            description="Task",
            steps=[TaskStep(step_id=1, tool="safe_tool", status=StepStatus.COMPLETED)],
        )
        with self.assertRaises(TypeError):
            evaluate_approval_compliance(task, registry="not_a_registry")
        with self.assertRaises(TypeError):
            evaluate_approval_compliance(task, logs="not_a_list")


if __name__ == "__main__":
    unittest.main()
