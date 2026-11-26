"""Service bridge connecting Hermes requests to authoritative project modules."""

from typing import Any

from src.automation.models import StepStatus, TaskStatus
from src.automation_agent import AutomationAgent
from src.hermes.config import HermesConfig
from src.hermes.protocol import HermesRequest, HermesRequestStatus, HermesResponse


class HermesService:
    def __init__(
        self,
        agent: AutomationAgent,
        task_store=None,
        logger=None,
        config: HermesConfig | None = None,
    ):
        self.agent = agent
        self.task_store = task_store or getattr(agent.executor, "task_store", None)
        self.logger = logger or getattr(agent, "logger", None)
        self.config = config or HermesConfig()

    def _log_event(
        self,
        task_id: str,
        event: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        if self.logger and hasattr(self.logger, "log_event"):
            try:
                self.logger.log_event(task_id=task_id, event=event, details=details)
            except Exception:
                pass

    def handle_request(self, request: HermesRequest) -> HermesResponse:
        """Route and execute a HermesRequest against authoritative core systems."""
        operation = request.operation

        if operation == "run_automation":
            return self._handle_run_automation(request)
        elif operation == "query_knowledge":
            return self._handle_query_knowledge(request)
        elif operation == "get_task_status":
            return self._handle_get_task_status(request)
        elif operation == "resume_task":
            return self._handle_resume_task(request)
        else:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.REJECTED,
                message=f"Unsupported operation: {operation}",
            )

    def _handle_run_automation(self, request: HermesRequest) -> HermesResponse:
        use_rag = bool(request.arguments.get("use_rag", False))
        knowledge_dependent = bool(request.arguments.get("knowledge_dependent", False))

        try:
            result = self.agent.run(
                request.message,
                use_rag=use_rag,
                knowledge_dependent=knowledge_dependent,
            )
        except Exception as error:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message="Automation planning or execution failed",
                error=f"{type(error).__name__}: {error}",
            )

        task_id = result.task_id

        self._log_event(
            task_id,
            "hermes_request_started",
            details={
                "request_id": request.request_id,
                "operation": request.operation,
            },
        )

        if result.status == TaskStatus.COMPLETED:
            self._log_event(
                task_id,
                "hermes_request_completed",
                details={"request_id": request.request_id, "status": "completed"},
            )
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.COMPLETED,
                message="Task completed successfully",
                task_id=task_id,
                data={
                    "status": result.status.value,
                    "description": result.description,
                    "output": result.steps[-1].output if result.steps else None,
                },
            )
        elif result.status == TaskStatus.AWAITING_APPROVAL:
            self._log_event(
                task_id,
                "hermes_approval_required",
                details={"request_id": request.request_id},
            )
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.AWAITING_APPROVAL,
                message="Task requires human approval for sensitive action",
                task_id=task_id,
            )
        else:
            step_errors = [s.error for s in result.steps if s.error]
            err = step_errors[0] if step_errors else "Execution halted"
            self._log_event(
                task_id,
                "hermes_request_failed",
                details={"request_id": request.request_id, "error": err},
            )
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message=f"Task ended with status {result.status.value}",
                task_id=task_id,
                error=err,
            )

    def _handle_query_knowledge(self, request: HermesRequest) -> HermesResponse:
        retriever = getattr(self.agent, "rag_retriever", None)
        if retriever is None:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message="RAG retriever is not configured on this agent",
            )

        try:
            context = retriever.retrieve(request.message)
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.COMPLETED,
                message="Knowledge query retrieved successfully",
                data={
                    "query": request.message,
                    "chunks": [
                        {
                            "content": c.content,
                            "source": c.source,
                            "score": c.score,
                        }
                        for c in context.chunks
                    ],
                    "sources": context.sources,
                    "scores": context.scores,
                    "error": context.error,
                },
            )
        except Exception as error:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message="Retrieval query failed",
                error=f"{type(error).__name__}: {error}",
            )

    def _handle_get_task_status(self, request: HermesRequest) -> HermesResponse:
        task_id = request.arguments.get("task_id") or request.message
        if not self.task_store:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message="Task store is not configured",
            )

        task = self.task_store.get_task(task_id)
        if task is None:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message=f"Task not found: {task_id}",
            )

        completed_count = sum(
            1 for s in task.steps if s.status == StepStatus.COMPLETED
        )

        return HermesResponse(
            request_id=request.request_id,
            status=HermesRequestStatus.COMPLETED,
            message=f"Task status is {task.status.value}",
            task_id=task.task_id,
            data={
                "task_id": task.task_id,
                "status": task.status.value,
                "description": task.description,
                "total_steps": len(task.steps),
                "completed_steps": completed_count,
                "awaiting_approval": task.status == TaskStatus.AWAITING_APPROVAL,
            },
        )

    def _handle_resume_task(self, request: HermesRequest) -> HermesResponse:
        task_id = request.arguments.get("task_id") or request.message
        if not self.task_store:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message="Task store is not configured",
            )

        task = self.task_store.get_task(task_id)
        if task is None:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message=f"Task not found: {task_id}",
            )

        if task.status == TaskStatus.COMPLETED:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message=f"Cannot resume already completed task: {task_id}",
                task_id=task_id,
            )

        try:
            resumed = self.agent.executor.resume(task_id)
            return HermesResponse(
                request_id=request.request_id,
                status=(
                    HermesRequestStatus.COMPLETED
                    if resumed.status == TaskStatus.COMPLETED
                    else HermesRequestStatus.FAILED
                ),
                message=f"Task resumed with final status {resumed.status.value}",
                task_id=task_id,
                data={
                    "task_id": task_id,
                    "status": resumed.status.value,
                    "output": resumed.steps[-1].output if resumed.steps else None,
                },
            )
        except Exception as error:
            return HermesResponse(
                request_id=request.request_id,
                status=HermesRequestStatus.FAILED,
                message="Resume execution failed",
                task_id=task_id,
                error=f"{type(error).__name__}: {error}",
            )
