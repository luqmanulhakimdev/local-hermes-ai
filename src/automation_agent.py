from src.automation.planner import TaskPlanner, MAX_PLANNER_REQUEST_SIZE
from src.automation.tool_setup import create_tool_registry
from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger
from src.automation.config import AutomationConfig


class AutomationAgent:
    def __init__(
        self,
        planner=None,
        registry=None,
        logger=None,
        config: AutomationConfig | None = None,
        rag_retriever=None,
    ):
        if config is not None and not isinstance(config, AutomationConfig):
            raise TypeError("config must be an AutomationConfig")
        self.config = config or AutomationConfig()
        self.planner = planner or TaskPlanner()
        self.registry = registry or create_tool_registry()
        self.logger = logger or TaskLogger(db_path=self.config.db_path)
        self.rag_retriever = rag_retriever

        self.executor = TaskExecutor(
            registry=self.registry,
            logger=self.logger,
            config=self.config,
        )

    def run(
        self,
        user_request: str,
        use_rag: bool = False,
        knowledge_dependent: bool = False,
        retrieval_query: str | None = None,
    ):
        if not isinstance(user_request, str) or not user_request.strip():
            raise ValueError("Task description must not be empty")

        if len(user_request) > MAX_PLANNER_REQUEST_SIZE:
            raise ValueError(
                f"Task description exceeds maximum allowed length of {MAX_PLANNER_REQUEST_SIZE} characters"
            )

        context = None
        query = retrieval_query if retrieval_query is not None else user_request

        if use_rag:
            if self.rag_retriever is not None:
                context = self.rag_retriever.retrieve(query)
            elif knowledge_dependent:
                raise ValueError(
                    "Unable to create plan: RAG retriever is not configured for knowledge-dependent task"
                )

        # 1. Generate task plan
        if use_rag or context is not None or knowledge_dependent:
            task = self.planner.plan(
                user_request,
                context=context,
                knowledge_dependent=knowledge_dependent,
            )
        else:
            task = self.planner.plan(user_request)

        if context is not None and hasattr(self.logger, "log_event"):
            self.logger.log_event(
                task.task_id,
                "rag_context_attached",
                details={
                    "query": query,
                    "chunks_found": len(context.chunks),
                    "sources": context.sources,
                    "scores": context.scores,
                    "error": context.error,
                },
            )

        # 2. Execute task
        result = self.executor.execute(task)

        return result


def main():
    agent = AutomationAgent()

    print("=" * 50)
    print("LOCAL AI AUTOMATION AGENT")
    print("Powered by Ollama")
    print("Type 'exit' to quit")
    print("=" * 50)

    while True:
        try:
            user_request = input("\nWhat should I do? ").strip()

            if user_request.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            if not user_request:
                continue

            print("\nPlanning and executing task...")

            result = agent.run(user_request)

            print(f"\nTask ID: {result.task_id}")
            print(f"Status: {result.status.value}")

            for step in result.steps:
                print(f"\nStep {step.step_id}: {step.tool}")
                print(f"Status: {step.status.value}")

                if step.status.value == "completed":
                    print("Output:")
                    print(step.output)
                else:
                    print(f"Error: {step.error}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except Exception as error:
            print(f"\nAgent error: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()