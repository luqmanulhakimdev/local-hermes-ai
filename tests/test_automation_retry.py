import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.automation.config import RetryPolicy
from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger
from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestRetryPolicy(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

    def tearDown(self):
        self.temp_dir.cleanup()
    def test_retry_policy_validation(self):
        policy = RetryPolicy(max_attempts=3, delay_seconds=0.1)
        self.assertEqual(policy.max_attempts, 3)
        self.assertEqual(policy.delay_seconds, 0.1)

        # Invalid max_attempts
        with self.assertRaises(ValueError):
            RetryPolicy(max_attempts=0)
        with self.assertRaises(ValueError):
            RetryPolicy(max_attempts=6)
        with self.assertRaises(TypeError):
            RetryPolicy(max_attempts=2.5)
        with self.assertRaises(TypeError):
            RetryPolicy(max_attempts=True)

        # Invalid delay_seconds
        with self.assertRaises(ValueError):
            RetryPolicy(delay_seconds=-0.5)
        with self.assertRaises(TypeError):
            RetryPolicy(delay_seconds="0.1")
        with self.assertRaises(TypeError):
            RetryPolicy(delay_seconds=False)

    def test_transient_failure_then_success(self):
        registry = ToolRegistry()
        call_count = 0

        def flaky_tool():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError("Temporary timeout")
            return "recovered"

        registry.register(
            ToolDefinition(
                name="flaky",
                description="Flaky tool",
                handler=flaky_tool,
                required_arguments=set(),
            )
        )

        task_store = TaskStore(self.db_path)
        logger = TaskLogger(self.db_path)
        sleeper = MagicMock()

        executor = TaskExecutor(
            registry=registry,
            task_store=task_store,
            logger=logger,
            retry_policy=RetryPolicy(max_attempts=3, delay_seconds=0.05),
            sleeper=sleeper,
        )

        task = TaskPlan(
            description="Test retry",
            steps=[TaskStep(step_id=1, tool="flaky")],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(result.steps[0].output, "recovered")
        self.assertEqual(call_count, 2)
        sleeper.assert_called_once_with(0.05)

        # Verify retry was logged
        logs = logger.get_task_logs(task.task_id)
        retry_logs = [l for l in logs if l["event"] == "step_retry"]
        self.assertEqual(len(retry_logs), 1)
        self.assertEqual(retry_logs[0]["step_id"], 1)

    def test_exhausted_retries_fails_task(self):
        registry = ToolRegistry()
        call_count = 0

        def failing_tool():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("Always times out")

        registry.register(
            ToolDefinition(
                name="always_fails",
                description="Failing tool",
                handler=failing_tool,
                required_arguments=set(),
            )
        )

        task_store = TaskStore(self.db_path)
        logger = TaskLogger(self.db_path)
        sleeper = MagicMock()

        executor = TaskExecutor(
            registry=registry,
            task_store=task_store,
            logger=logger,
            retry_policy=RetryPolicy(max_attempts=2, delay_seconds=0.01),
            sleeper=sleeper,
        )

        task = TaskPlan(
            description="Test exhausted retry",
            steps=[TaskStep(step_id=1, tool="always_fails")],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(result.steps[0].status, StepStatus.FAILED)
        self.assertEqual(call_count, 2)
        self.assertIn("Always times out", result.steps[0].error)

        logs = logger.get_task_logs(task.task_id)
        retry_logs = [l for l in logs if l["event"] == "step_retry"]
        self.assertEqual(len(retry_logs), 1)

    def test_non_retryable_error_fails_immediately(self):
        registry = ToolRegistry()
        call_count = 0

        def bad_value_tool():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid argument value")

        registry.register(
            ToolDefinition(
                name="bad_tool",
                description="Bad tool",
                handler=bad_value_tool,
                required_arguments=set(),
            )
        )

        task_store = TaskStore(self.db_path)
        logger = TaskLogger(self.db_path)
        sleeper = MagicMock()

        executor = TaskExecutor(
            registry=registry,
            task_store=task_store,
            logger=logger,
            retry_policy=RetryPolicy(max_attempts=3, delay_seconds=0.05),
            sleeper=sleeper,
        )

        task = TaskPlan(
            description="Test non-retryable",
            steps=[TaskStep(step_id=1, tool="bad_tool")],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(call_count, 1)  # Only 1 attempt, no retry
        sleeper.assert_not_called()

        logs = logger.get_task_logs(task.task_id)
        retry_logs = [l for l in logs if l["event"] == "step_retry"]
        self.assertEqual(len(retry_logs), 0)

    def test_approval_sensitive_tool_is_never_retried(self):
        registry = ToolRegistry()
        call_count = 0

        def sensitive_tool():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("Sensitive timed out")

        registry.register(
            ToolDefinition(
                name="sensitive_action",
                description="Sensitive action",
                handler=sensitive_tool,
                required_arguments=set(),
                requires_approval=True,
            )
        )

        task_store = TaskStore(self.db_path)
        logger = TaskLogger(self.db_path)
        sleeper = MagicMock()

        executor = TaskExecutor(
            registry=registry,
            task_store=task_store,
            logger=logger,
            retry_policy=RetryPolicy(max_attempts=3, delay_seconds=0.05),
            approval_handler=lambda t, s, a: True,
            sleeper=sleeper,
        )

        task = TaskPlan(
            description="Test approval retry protection",
            steps=[TaskStep(step_id=1, tool="sensitive_action")],
        )

        result = executor.execute(task)

        self.assertEqual(result.status, TaskStatus.FAILED)
        self.assertEqual(call_count, 1)  # Approval-sensitive tools must NOT be retried
        sleeper.assert_not_called()

        logs = logger.get_task_logs(task.task_id)
        retry_logs = [l for l in logs if l["event"] == "step_retry"]
        self.assertEqual(len(retry_logs), 0)


if __name__ == "__main__":
    unittest.main()
