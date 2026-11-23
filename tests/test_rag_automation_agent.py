import unittest
from unittest.mock import Mock

from src.automation_agent import AutomationAgent
from src.automation.models import TaskPlan, TaskStatus, TaskStep
from src.automation.rag_context import ContextChunk, RetrievedContext
from src.automation.registry import ToolDefinition, ToolRegistry


class TestRAGAutomationAgent(unittest.TestCase):
    def setUp(self):
        self.task = TaskPlan(
            description="Test automation with RAG",
            steps=[
                TaskStep(
                    step_id=1,
                    tool="test_tool",
                    arguments={},
                )
            ],
        )

        self.planner = Mock()
        self.planner.plan.return_value = self.task

        self.registry = ToolRegistry()
        self.registry.register(
            ToolDefinition(
                name="test_tool",
                description="Test tool",
                handler=lambda: "test output",
                required_arguments=set(),
                requires_approval=False,
            )
        )

        self.logger = Mock()
        self.retriever = Mock()

        self.agent = AutomationAgent(
            planner=self.planner,
            registry=self.registry,
            logger=self.logger,
            rag_retriever=self.retriever,
        )

    def test_run_without_rag_does_not_call_retriever(self):
        result = self.agent.run("Run simple task")
        self.retriever.retrieve.assert_not_called()
        self.planner.plan.assert_called_once_with("Run simple task")
        self.assertEqual(result.status, TaskStatus.COMPLETED)

    def test_run_with_rag_retrieves_and_passes_context_to_planner(self):
        chunk = ContextChunk(content="Project has 387 tests", source="test.md", score=0.95)
        context = RetrievedContext(query="test count", chunks=[chunk])
        self.retriever.retrieve.return_value = context

        result = self.agent.run("Calculate double tests", use_rag=True)

        self.retriever.retrieve.assert_called_once_with("Calculate double tests")
        self.planner.plan.assert_called_once_with(
            "Calculate double tests",
            context=context,
            knowledge_dependent=False,
        )
        self.assertEqual(result.status, TaskStatus.COMPLETED)

        # Verify event logging
        self.logger.log_event.assert_any_call(
            self.task.task_id,
            "rag_context_attached",
            details={
                "query": "Calculate double tests",
                "chunks_found": 1,
                "sources": ["test.md"],
                "scores": [0.95],
                "error": None,
            },
        )

    def test_run_with_rag_custom_retrieval_query(self):
        context = RetrievedContext(query="custom query", chunks=[])
        self.retriever.retrieve.return_value = context

        self.agent.run(
            "Plan my work",
            use_rag=True,
            retrieval_query="custom query",
        )

        self.retriever.retrieve.assert_called_once_with("custom query")
        self.planner.plan.assert_called_once_with(
            "Plan my work",
            context=context,
            knowledge_dependent=False,
        )

    def test_run_knowledge_dependent_without_retriever_fails(self):
        agent_no_rag = AutomationAgent(
            planner=self.planner,
            registry=self.registry,
            logger=self.logger,
            rag_retriever=None,
        )

        with self.assertRaises(ValueError) as ctx:
            agent_no_rag.run(
                "Must use project docs",
                use_rag=True,
                knowledge_dependent=True,
            )
        self.assertIn("RAG retriever is not configured", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
