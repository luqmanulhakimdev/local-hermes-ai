import tempfile
import unittest
from pathlib import Path

from src.automation.config import AutomationConfig
from src.automation.health import check_production_health
from src.automation.logger import TaskLogger
from src.automation.planner import TaskPlanner
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore


class TestProductionHealth(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="test_tool",
                description="Test tool",
                handler=lambda: "ok",
                required_arguments=set(),
            )
        )
        self.task_store = TaskStore(self.db_path)
        self.logger = TaskLogger(self.db_path)
        self.planner = TaskPlanner()
        self.config = AutomationConfig(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_healthy_runtime_configuration(self):
        result = check_production_health(
            config=self.config,
            registry=self.registry,
            task_store=self.task_store,
            logger=self.logger,
            planner=self.planner,
        )
        self.assertTrue(result.healthy)
        self.assertTrue(result.checks["config"])
        self.assertTrue(result.checks["registry"])
        self.assertTrue(result.checks["task_store"])
        self.assertTrue(result.checks["logger"])
        self.assertTrue(result.checks["planner"])

    def test_empty_registry_is_unhealthy(self):
        empty_registry = ToolRegistry()
        result = check_production_health(
            config=self.config,
            registry=empty_registry,
            task_store=self.task_store,
            logger=self.logger,
            planner=self.planner,
        )
        self.assertFalse(result.healthy)
        self.assertFalse(result.checks["registry"])

    def test_missing_components_are_unhealthy(self):
        result = check_production_health(
            config=self.config,
            registry=None,
            task_store=None,
            logger=None,
            planner=None,
        )
        self.assertFalse(result.healthy)
        self.assertFalse(result.checks["registry"])
        self.assertFalse(result.checks["task_store"])
        self.assertFalse(result.checks["logger"])
        self.assertFalse(result.checks["planner"])


if __name__ == "__main__":
    unittest.main()
