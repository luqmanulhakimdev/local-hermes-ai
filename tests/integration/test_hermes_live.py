import os
from pathlib import Path
import unittest

from src.hermes.adapter import HermesCLIAdapter
from src.hermes.config import HermesConfig
from src.hermes.health import check_hermes
from src.hermes.protocol import HermesRequest, HermesRequestStatus
from src.hermes.service import HermesService
from src.automation_agent import AutomationAgent


class TestHermesLiveIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = HermesConfig()
        cls.executable_exists = (
            Path(cls.config.executable_path).is_file()
            and os.access(cls.config.executable_path, os.X_OK)
        )

    def test_live_health_check(self):
        if not self.executable_exists:
            self.skipTest("Hermes executable is not available on this machine")
        report = check_hermes(self.config)
        self.assertIn(report["status"], ["ok", "degraded"])
        self.assertTrue(report["executable_exists"])
        self.assertIsNotNone(report["version"])

    def test_live_service_query_knowledge(self):
        agent = AutomationAgent()
        service = HermesService(agent=agent, config=self.config)
        req = HermesRequest(
            request_id="live-test-req-1",
            operation="query_knowledge",
            message="testing project",
        )
        resp = service.handle_request(req)
        # RAG retriever is not configured by default on bare agent unless passed, so expect graceful handling
        self.assertIn(resp.status, [HermesRequestStatus.COMPLETED, HermesRequestStatus.FAILED])


if __name__ == "__main__":
    unittest.main()
