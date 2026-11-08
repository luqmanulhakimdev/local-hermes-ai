import tempfile
import unittest
from pathlib import Path

from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger
from src.automation.models import TaskPlan, TaskStep, TaskStatus
from src.automation.registry import ToolDefinition, ToolRegistry


class TestExecutorLogging(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "automation.db"

        self.logger = TaskLogger(db_path=db_path)

        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="greet",
                description="Return a greeting",
                handler=lambda name: f"Halo, {name}!",
                required_arguments={"name"},
            )
        )

        self.executor = TaskExecutor(
            registry=self.registry,
            logger=self.logger,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_successful_task_is_logged(self):
        task = TaskPlan(
            description="Test logging",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="greet",
                    arguments={"name": "AI Engineering"},
                )
            ],
        )

        result = self.executor.execute(task)
        logs = self.logger.get_task_logs(task.task_id)

        events = [log["event"] for log in logs]

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(
            events,
            [
                "task_started",
                "step_started",
                "step_completed",
                "task_completed",
            ],
        )

    def test_failed_task_is_logged(self):
        task = TaskPlan(
            description="Test failed task",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="unknown_tool",
                    arguments={},
                )
            ],
        )

        result = self.executor.execute(task)
        logs = self.logger.get_task_logs(task.task_id)

        events = [log["event"] for log in logs]

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(
            events,
            [
                "task_started",
                "step_failed",
                "task_failed",
            ],
        )

        self.assertIsNotNone(result.steps[0].error)

    def test_step_output_is_logged(self):
        task = TaskPlan(
            description="Test output logging",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="greet",
                    arguments={"name": "Hermes"},
                )
            ],
        )

        self.executor.execute(task)
        logs = self.logger.get_task_logs(task.task_id)

        completed_log = next(
            log for log in logs
            if log["event"] == "step_completed"
        )

        self.assertEqual(
            completed_log["details"]["output"],
            "Halo, Hermes!",
        )

    def test_approval_granted_is_logged(self):
        registry = ToolRegistry()

        registry.register(
            ToolDefinition(
                name="dangerous_tool",
                description="A tool requiring approval",
                handler=lambda **arguments: "executed",
                required_arguments={"value"},
                requires_approval=True,
            )
        )

        logger = TaskLogger()

        executor = TaskExecutor(
            registry,
            logger=logger,
            approval_handler=lambda task, step, arguments: True,
        )

        task = TaskPlan(
            description="Approval logging test",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="dangerous_tool",
                    arguments={"value": "hello"},
                )
            ],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.COMPLETED)

        logs = logger.get_task_logs(task.task_id)
        events = [log["event"] for log in logs]

        self.assertEqual(
            events,
            [
                "task_started",
                "step_started",
                "approval_requested",
                "approval_granted",
                "step_completed",
                "task_completed",
            ],
        )


    def test_approval_denied_is_logged(self):
        executed = []

        registry = ToolRegistry()

        registry.register(
            ToolDefinition(
                name="dangerous_tool",
                description="A tool requiring approval",
                handler=lambda **arguments: executed.append(arguments),
                required_arguments={"value"},
                requires_approval=True,
            )
        )

        logger = TaskLogger()

        executor = TaskExecutor(
            registry,
            logger=logger,
            approval_handler=lambda task, step, arguments: False,
        )

        task = TaskPlan(
            description="Approval denial logging test",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="dangerous_tool",
                    arguments={"value": "hello"},
                )
            ],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(executed, [])

        logs = logger.get_task_logs(task.task_id)
        events = [log["event"] for log in logs]

        self.assertEqual(
            events,
            [
                "task_started",
                "step_started",
                "approval_requested",
                "approval_denied",
                "step_failed",
                "task_failed",
            ],
        )


if __name__ == "__main__":
    unittest.main()