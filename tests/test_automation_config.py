import unittest
from pathlib import Path

from src.automation.config import AutomationConfig
from src.automation.executor import TaskExecutor
from src.automation.registry import ToolRegistry
from src.automation_agent import AutomationAgent


class TestAutomationConfig(unittest.TestCase):
    def test_default_configuration_is_valid(self):
        config = AutomationConfig()
        self.assertEqual(config.tool_timeout, 30.0)
        self.assertEqual(config.max_output_size, 20_000)
        self.assertEqual(config.max_task_steps, 5)
        self.assertTrue(config.require_approval_for_sensitive_tools)
        self.assertIsNone(config.db_path)

    def test_custom_valid_configuration(self):
        config = AutomationConfig(
            tool_timeout=10.5,
            max_output_size=5_000,
            max_task_steps=3,
            require_approval_for_sensitive_tools=False,
            db_path="data/test.db",
        )
        self.assertEqual(config.tool_timeout, 10.5)
        self.assertEqual(config.max_output_size, 5_000)
        self.assertEqual(config.max_task_steps, 3)
        self.assertFalse(config.require_approval_for_sensitive_tools)
        self.assertEqual(config.db_path, Path("data/test.db"))

    def test_invalid_timeout_rejected(self):
        with self.assertRaises(ValueError):
            AutomationConfig(tool_timeout=0)
        with self.assertRaises(ValueError):
            AutomationConfig(tool_timeout=-5.0)
        with self.assertRaises(TypeError):
            AutomationConfig(tool_timeout="30")
        with self.assertRaises(TypeError):
            AutomationConfig(tool_timeout=True)

    def test_invalid_max_output_size_rejected(self):
        with self.assertRaises(ValueError):
            AutomationConfig(max_output_size=0)
        with self.assertRaises(ValueError):
            AutomationConfig(max_output_size=-100)
        with self.assertRaises(TypeError):
            AutomationConfig(max_output_size=10.5)
        with self.assertRaises(TypeError):
            AutomationConfig(max_output_size="1000")
        with self.assertRaises(TypeError):
            AutomationConfig(max_output_size=True)

    def test_invalid_max_task_steps_rejected(self):
        with self.assertRaises(ValueError):
            AutomationConfig(max_task_steps=0)
        with self.assertRaises(ValueError):
            AutomationConfig(max_task_steps=6)  # Cannot exceed MAX_TASK_STEPS = 5
        with self.assertRaises(ValueError):
            AutomationConfig(max_task_steps=-1)
        with self.assertRaises(TypeError):
            AutomationConfig(max_task_steps=3.5)
        with self.assertRaises(TypeError):
            AutomationConfig(max_task_steps="5")
        with self.assertRaises(TypeError):
            AutomationConfig(max_task_steps=False)

    def test_invalid_approval_boolean_rejected(self):
        with self.assertRaises(TypeError):
            AutomationConfig(require_approval_for_sensitive_tools=1)
        with self.assertRaises(TypeError):
            AutomationConfig(require_approval_for_sensitive_tools="yes")
        with self.assertRaises(TypeError):
            AutomationConfig(require_approval_for_sensitive_tools=None)

    def test_invalid_db_path_rejected(self):
        with self.assertRaises(ValueError):
            AutomationConfig(db_path="")
        with self.assertRaises(ValueError):
            AutomationConfig(db_path="   ")
        with self.assertRaises(TypeError):
            AutomationConfig(db_path=123)

    def test_executor_accepts_config(self):
        registry = ToolRegistry()
        config = AutomationConfig(
            tool_timeout=15.0,
            max_output_size=1_000,
        )
        executor = TaskExecutor(registry=registry, config=config)
        self.assertEqual(executor.tool_timeout, 15.0)
        self.assertEqual(executor.max_output_size, 1_000)
        self.assertEqual(executor.config, config)

    def test_agent_accepts_config(self):
        config = AutomationConfig(
            tool_timeout=25.0,
            max_output_size=2_000,
        )
        agent = AutomationAgent(config=config)
        self.assertEqual(agent.config, config)
        self.assertEqual(agent.executor.tool_timeout, 25.0)
        self.assertEqual(agent.executor.max_output_size, 2_000)


if __name__ == "__main__":
    unittest.main()
