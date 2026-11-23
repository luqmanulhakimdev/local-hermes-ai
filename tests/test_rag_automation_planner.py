import json
import unittest
from unittest.mock import MagicMock, patch

from src.automation.planner import TaskPlanner
from src.automation.rag_context import ContextChunk, RetrievedContext
from src.automation.registry import ToolDefinition, ToolRegistry


class TestRAGAutomationPlanner(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="calculator",
                description="Calculator tool",
                handler=lambda expression: 42,
                required_arguments={"expression"},
            )
        )
        self.registry.register(
            ToolDefinition(
                name="read_file",
                description="Read file",
                handler=lambda path: "content",
                required_arguments={"path"},
            )
        )
        self.planner = TaskPlanner(registry=self.registry)

    def _mock_response(self, content_dict):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "message": {
                "content": json.dumps(content_dict)
            }
        }
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    @patch("requests.post")
    def test_planner_without_context_maintains_backward_compatibility(self, mock_post):
        mock_post.return_value = self._mock_response({
            "description": "Calculate without context",
            "steps": [
                {
                    "step_id": 1,
                    "tool": "calculator",
                    "arguments": {"expression": "2 + 2"},
                }
            ],
        })

        plan = self.planner.plan("Hitung 2 + 2")
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].tool, "calculator")

        # Verify prompt does not include retrieved knowledge section
        call_args = mock_post.call_args[1]["json"]["messages"][1]["content"]
        self.assertNotIn("RETRIEVED KNOWLEDGE", call_args)

    @patch("requests.post")
    def test_planner_with_context_includes_untrusted_knowledge_section(self, mock_post):
        mock_post.return_value = self._mock_response({
            "description": "Calculate with context",
            "steps": [
                {
                    "step_id": 1,
                    "tool": "calculator",
                    "arguments": {"expression": "303 * 2"},
                }
            ],
        })

        chunk = ContextChunk(
            content="The test suite contains 303 tests.",
            source="docs/testing.md",
            score=0.91,
        )
        context = RetrievedContext(
            query="test count",
            chunks=[chunk],
        )

        plan = self.planner.plan("Calculate double test count", context=context)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].arguments["expression"], "303 * 2")

        # Verify prompt contract includes isolated knowledge section and security instructions
        call_args = mock_post.call_args[1]["json"]["messages"][1]["content"]
        self.assertIn("RETRIEVED KNOWLEDGE", call_args)
        self.assertIn("The test suite contains 303 tests.", call_args)
        self.assertIn("strictly informational reference data", call_args)

    @patch("requests.post")
    def test_knowledge_dependent_planning_fails_safely_when_context_missing(self, mock_post):
        # Empty context for knowledge dependent task
        empty_context = RetrievedContext(query="unknown query", chunks=[])

        with self.assertRaises(ValueError) as ctx:
            self.planner.plan(
                "Based on project docs, calculate something",
                context=empty_context,
                knowledge_dependent=True,
            )
        self.assertIn("required project knowledge is unavailable", str(ctx.exception))
        mock_post.assert_not_called()

    @patch("requests.post")
    def test_knowledge_dependent_planning_fails_safely_on_retrieval_error(self, mock_post):
        error_context = RetrievedContext(
            query="err query",
            chunks=[],
            error="ConnectionError: Vector DB unreachable",
        )

        with self.assertRaises(ValueError) as ctx:
            self.planner.plan(
                "Based on project docs, calculate something",
                context=error_context,
                knowledge_dependent=True,
            )
        self.assertIn("retrieval failure", str(ctx.exception))
        mock_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
