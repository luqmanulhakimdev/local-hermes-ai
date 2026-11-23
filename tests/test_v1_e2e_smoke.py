"""Deterministic End-to-End Smoke Test for Local Hermes AI v1.0."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.automation.config import AutomationConfig
from src.automation.evaluation import EvaluationMetrics
from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger
from src.automation.models import StepStatus, TaskPlan, TaskStatus, TaskStep
from src.automation.planner import TaskPlanner
from src.automation.rag_context import ContextChunk, RAGConfig, RAGContextRetriever
from src.automation.registry import ToolDefinition, ToolRegistry
from src.automation.task_store import TaskStore
from src.automation.tracing import build_task_trace
from src.automation.validator import TaskValidator
from src.automation_agent import AutomationAgent
from src.hermes.config import HermesConfig
from src.hermes.evaluation import evaluate_hermes_run
from src.hermes.protocol import HermesRequest, HermesRequestStatus
from src.hermes.service import HermesService
from src.rag.vector_store import VectorStore
from src.tools.calculator import calculate


class TestV1EndToEndSmoke(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.auto_db = str(self.temp_path / "automation.db")
        self.rag_db = str(self.temp_path / "rag.db")

        self.auto_config = AutomationConfig(db_path=Path(self.auto_db))
        self.hermes_config = HermesConfig()
        self.rag_config = RAGConfig(db_path=Path(self.rag_db), threshold=0.1)

        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="calculator",
                description="AST-based safe calculator",
                handler=calculate,
                required_arguments={"expression"},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="read_file",
                description="Read permitted document",
                handler=lambda path: "Document content: 460 tests passed in benchmark",
                required_arguments={"path"},
            )
        )

        self.validator = TaskValidator(registry=self.registry)
        self.task_store = TaskStore(config=self.auto_config)
        self.logger = TaskLogger(config=self.auto_config)

        self.vector_store = VectorStore(db_path=self.rag_db)
        self.retriever = RAGContextRetriever(
            vector_store=self.vector_store,
            config=self.rag_config,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _mock_planner_response(self, content_dict):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {
                "content": json.dumps(content_dict)
            }
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @patch("src.rag.vector_store.embed_text")
    @patch("requests.post")
    def test_complete_end_to_end_v1_pipeline(self, mock_post, mock_embed):
        # 1. Populate VectorStore with project document chunk
        mock_embed.return_value = [1.0, 0.0]
        self.vector_store.add_chunks(
            ["The baseline test count is 460 tests."],
            source="docs/testing.md",
        )

        # 2. Mock planner to output plan based on retrieved context
        mock_post.return_value = self._mock_planner_response({
            "description": "Double the baseline test count",
            "steps": [
                {
                    "step_id": 1,
                    "tool": "calculator",
                    "arguments": {"expression": "460 * 2"},
                }
            ],
        })

        # 3. Instantiate full architecture stack
        planner = TaskPlanner(registry=self.registry)
        agent = AutomationAgent(
            planner=planner,
            registry=self.registry,
            logger=self.logger,
            config=self.auto_config,
            rag_retriever=self.retriever,
        )
        service = HermesService(
            agent=agent,
            task_store=self.task_store,
            logger=self.logger,
            config=self.hermes_config,
        )

        # 4. Dispatch user request through Hermes integration
        request = HermesRequest(
            request_id="v1-smoke-001",
            operation="run_automation",
            message="Calculate double the baseline test count using project docs",
            arguments={"use_rag": True, "knowledge_dependent": True},
        )

        response = service.handle_request(request)

        # 5. Assert successful response
        self.assertEqual(response.status, HermesRequestStatus.COMPLETED)
        self.assertIsNotNone(response.task_id)
        task_id = response.task_id
        self.assertEqual(response.data["output"], 920)

        # 6. Assert persistence in SQLite TaskStore
        persisted_task = self.task_store.get_task(task_id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.status, TaskStatus.COMPLETED)
        self.assertEqual(len(persisted_task.steps), 1)
        self.assertEqual(persisted_task.steps[0].status, StepStatus.COMPLETED)
        self.assertEqual(persisted_task.steps[0].output, 920)

        # 7. Assert structured audit logs in SQLite TaskLogger
        logs = self.logger.get_task_logs(task_id)
        events = [log["event"] for log in logs]
        self.assertIn("rag_context_attached", events)
        self.assertIn("step_started", events)
        self.assertIn("step_completed", events)
        self.assertIn("task_completed", events)
        self.assertIn("hermes_request_completed", events)

        # 8. Assert trace completeness
        trace = build_task_trace(logs=logs)
        self.assertTrue(trace.completed)
        self.assertEqual(len(trace.steps), 1)
        self.assertTrue(trace.steps[1].completed)

        # 9. Assert evaluation metrics
        metrics = EvaluationMetrics.from_task(
            task=persisted_task,
            plan_valid=True,
            logs=logs,
            registry=self.registry,
        )
        self.assertTrue(metrics.plan_valid)
        self.assertTrue(metrics.task_success)
        self.assertEqual(metrics.step_success_rate, 1.0)
        self.assertTrue(metrics.trace_complete)

        # 10. Assert Hermes run evaluation metrics
        hermes_metrics = evaluate_hermes_run(
            request=request,
            response=response,
            logs=logs,
        )
        self.assertTrue(hermes_metrics.hermes_request_success)
        self.assertTrue(hermes_metrics.hermes_adapter_success)
        self.assertTrue(hermes_metrics.hermes_to_automation_success)
        self.assertTrue(hermes_metrics.trace_complete)


if __name__ == "__main__":
    unittest.main()
