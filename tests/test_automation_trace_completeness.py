import unittest

from src.automation.evaluation import evaluate_trace_completeness
from src.automation.models import TaskPlan, TaskStatus, TaskStep, StepStatus


class TestTraceCompletenessEvaluation(unittest.TestCase):
    def test_complete_successful_trace(self):
        task = TaskPlan(
            task_id="t1",
            description="Complete task",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        logs = [
            {"event": "task_started", "task_id": "t1"},
            {"event": "step_started", "task_id": "t1", "step_id": 1},
            {"event": "step_completed", "task_id": "t1", "step_id": 1},
            {"event": "step_started", "task_id": "t1", "step_id": 2},
            {"event": "step_completed", "task_id": "t1", "step_id": 2},
            {"event": "task_completed", "task_id": "t1"},
        ]
        self.assertTrue(evaluate_trace_completeness(logs=logs, task=task))
        self.assertTrue(evaluate_trace_completeness(logs=logs, task=None))

    def test_complete_failed_trace(self):
        task = TaskPlan(
            task_id="t2",
            description="Failed task",
            steps=[
                TaskStep(step_id=1, tool="tool1", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="tool2", status=StepStatus.FAILED),
            ],
            status=TaskStatus.FAILED,
        )
        logs = [
            {"event": "task_started", "task_id": "t2"},
            {"event": "step_started", "task_id": "t2", "step_id": 1},
            {"event": "step_completed", "task_id": "t2", "step_id": 1},
            {"event": "step_started", "task_id": "t2", "step_id": 2},
            {"event": "step_failed", "task_id": "t2", "step_id": 2},
            {"event": "task_failed", "task_id": "t2"},
        ]
        self.assertTrue(evaluate_trace_completeness(logs=logs, task=task))

    def test_complete_approval_trace(self):
        task = TaskPlan(
            task_id="t3",
            description="Approval task",
            steps=[
                TaskStep(step_id=1, tool="safe_tool", status=StepStatus.COMPLETED),
                TaskStep(step_id=2, tool="sensitive_tool", status=StepStatus.COMPLETED),
            ],
            status=TaskStatus.COMPLETED,
        )
        logs = [
            {"event": "task_started", "task_id": "t3"},
            {"event": "step_started", "task_id": "t3", "step_id": 1},
            {"event": "step_completed", "task_id": "t3", "step_id": 1},
            {"event": "step_started", "task_id": "t3", "step_id": 2},
            {"event": "approval_requested", "task_id": "t3", "step_id": 2},
            {"event": "approval_granted", "task_id": "t3", "step_id": 2},
            {"event": "step_completed", "task_id": "t3", "step_id": 2},
            {"event": "task_completed", "task_id": "t3"},
        ]
        self.assertTrue(evaluate_trace_completeness(logs=logs, task=task))

    def test_incomplete_trace_missing_task_completed(self):
        logs = [
            {"event": "task_started", "task_id": "t4"},
            {"event": "step_started", "task_id": "t4", "step_id": 1},
            {"event": "step_completed", "task_id": "t4", "step_id": 1},
        ]
        self.assertFalse(evaluate_trace_completeness(logs=logs))

    def test_incomplete_trace_missing_step_completion(self):
        logs = [
            {"event": "task_started", "task_id": "t5"},
            {"event": "step_started", "task_id": "t5", "step_id": 1},
            {"event": "task_completed", "task_id": "t5"},
        ]
        self.assertFalse(evaluate_trace_completeness(logs=logs))

    def test_incomplete_trace_missing_task_started(self):
        logs = [
            {"event": "step_started", "task_id": "t6", "step_id": 1},
            {"event": "step_completed", "task_id": "t6", "step_id": 1},
            {"event": "task_completed", "task_id": "t6"},
        ]
        self.assertFalse(evaluate_trace_completeness(logs=logs))

    def test_unresolved_approval_request(self):
        logs = [
            {"event": "task_started", "task_id": "t7"},
            {"event": "step_started", "task_id": "t7", "step_id": 1},
            {"event": "approval_requested", "task_id": "t7", "step_id": 1},
            {"event": "task_completed", "task_id": "t7"},
        ]
        self.assertFalse(evaluate_trace_completeness(logs=logs))

    def test_empty_logs_returns_false(self):
        self.assertFalse(evaluate_trace_completeness(logs=[]))

    def test_invalid_types_raise_error(self):
        with self.assertRaises(TypeError):
            evaluate_trace_completeness(logs="not_a_list")
        with self.assertRaises(TypeError):
            evaluate_trace_completeness(logs=[{"event": "task_started"}], task="not_a_task")
        with self.assertRaises(TypeError):
            evaluate_trace_completeness(logs=["not_a_dict"])


if __name__ == "__main__":
    unittest.main()
