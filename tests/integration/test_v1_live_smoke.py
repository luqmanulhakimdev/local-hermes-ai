"""Live / Optional Smoke Tests for Local Hermes AI v1.0."""

import json
import os
from pathlib import Path
import unittest
import urllib.request

from src.automation.config import AutomationConfig
from src.automation.models import TaskStatus
from src.automation.planner import TaskPlanner
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation_agent import AutomationAgent
from src.hermes.config import HermesConfig
from src.hermes.health import check_hermes
from src.hermes.protocol import HermesRequest, HermesRequestStatus
from src.hermes.service import HermesService
from src.tools.calculator import calculate


class TestV1LiveSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hermes_config = HermesConfig()
        cls.hermes_available = (
            Path(cls.hermes_config.executable_path).is_file()
            and os.access(cls.hermes_config.executable_path, os.X_OK)
        )
        cls.ollama_available = False
        try:
            req = urllib.request.Request(
                f"{cls.hermes_config.ollama_base_url.rstrip('/')}/api/tags",
                headers={"User-Agent": "LocalHermesAI-LiveTest"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    cls.ollama_available = True
        except Exception:
            cls.ollama_available = False

    def test_live_ollama_endpoint_reachable(self):
        """Verify local Ollama service is running and exposes tags."""
        if not self.ollama_available:
            self.skipTest("Ollama is not running locally")
        report = check_hermes(self.hermes_config)
        self.assertTrue(report["ollama_reachable"])

    def test_live_hermes_cli_status(self):
        """Verify Hermes CLI binary is executable and outputs valid version."""
        if not self.hermes_available:
            self.skipTest("Hermes CLI is not installed locally")
        report = check_hermes(self.hermes_config)
        self.assertTrue(report["executable_exists"])
        self.assertIn("Hermes Agent", report["version"])

    def test_live_hermes_service_safe_execution(self):
        """Verify HermesService can plan and execute a safe task end-to-end with Ollama."""
        if not self.ollama_available:
            self.skipTest("Ollama is not running locally")

        agent = AutomationAgent()
        service = HermesService(agent=agent, config=self.hermes_config)

        req = HermesRequest(
            request_id="live-tools-001",
            operation="run_automation",
            message="What tools are available?",
        )
        resp = service.handle_request(req)
        self.assertEqual(resp.status, HermesRequestStatus.COMPLETED)
        self.assertIsNotNone(resp.task_id)
        self.assertIn("list_tools", resp.data["output"])


if __name__ == "__main__":
    unittest.main()
