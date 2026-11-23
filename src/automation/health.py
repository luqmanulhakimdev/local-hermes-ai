from dataclasses import dataclass
from pathlib import Path

from src.automation.config import AutomationConfig
from src.automation.logger import TaskLogger
from src.automation.planner import TaskPlanner
from src.automation.registry import ToolRegistry
from src.automation.task_store import TaskStore


@dataclass(frozen=True)
class HealthCheckResult:
    healthy: bool
    checks: dict[str, bool]
    details: dict[str, str]


def check_production_health(
    config: AutomationConfig | None = None,
    registry: ToolRegistry | None = None,
    task_store: TaskStore | None = None,
    logger: TaskLogger | None = None,
    planner: TaskPlanner | None = None,
) -> HealthCheckResult:
    checks = {}
    details = {}

    # 1. Config check
    try:
        cfg = config or AutomationConfig()
        checks["config"] = True
        details["config"] = (
            f"Valid (timeout={cfg.tool_timeout}s, max_output={cfg.max_output_size})"
        )
    except Exception as e:
        checks["config"] = False
        details["config"] = f"Invalid: {e}"

    # 2. Registry check
    if registry is None:
        checks["registry"] = False
        details["registry"] = "No tool registry provided"
    else:
        tools = registry.list_tools()
        if not tools:
            checks["registry"] = False
            details["registry"] = "Tool registry is empty"
        else:
            checks["registry"] = True
            details["registry"] = (
                f"Populated with {len(tools)} tools: {', '.join(tools)}"
            )

    # 3. Database / TaskStore check
    if task_store is None:
        checks["task_store"] = False
        details["task_store"] = "No task store provided"
    else:
        try:
            with task_store._connection() as conn:
                conn.execute("SELECT 1 FROM automation_tasks LIMIT 1")
            checks["task_store"] = True
            details["task_store"] = f"Connected to {task_store.db_path}"
        except Exception as e:
            checks["task_store"] = False
            details["task_store"] = f"Connection failed: {e}"

    # 4. Logger check
    if logger is None:
        checks["logger"] = False
        details["logger"] = "No logger provided"
    else:
        try:
            with logger._connection() as conn:
                conn.execute("SELECT 1 FROM automation_logs LIMIT 1")
            checks["logger"] = True
            details["logger"] = f"Connected to {logger.db_path}"
        except Exception as e:
            checks["logger"] = False
            details["logger"] = f"Connection failed: {e}"

    # 5. Planner check
    if planner is None:
        checks["planner"] = False
        details["planner"] = "No planner provided"
    else:
        checks["planner"] = True
        details["planner"] = f"Configured for model {planner.model}"

    overall_healthy = all(checks.values())
    return HealthCheckResult(
        healthy=overall_healthy,
        checks=checks,
        details=details,
    )
