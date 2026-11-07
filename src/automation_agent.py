from src.automation.planner import TaskPlanner
from src.automation.tool_setup import create_tool_registry
from src.automation.executor import TaskExecutor
from src.automation.logger import TaskLogger


class AutomationAgent:
    def __init__(
        self,
        planner=None,
        registry=None,
        logger=None,
    ):
        self.planner = planner or TaskPlanner()
        self.registry = registry or create_tool_registry()
        self.logger = logger or TaskLogger()

        self.executor = TaskExecutor(
            registry=self.registry,
            logger=self.logger,
        )

    def run(self, user_request: str):
        if not isinstance(user_request, str) or not user_request.strip():
            raise ValueError("Task description must not be empty")

        # 1. Generate task plan
        task = self.planner.plan(user_request)

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