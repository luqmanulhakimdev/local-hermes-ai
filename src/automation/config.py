from dataclasses import dataclass
from pathlib import Path

from src.automation.models import MAX_TASK_STEPS


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    delay_seconds: float = 0.0
    retryable_exceptions: tuple[type[Exception], ...] = (TimeoutError, ConnectionError)

    def __post_init__(self):
        if isinstance(self.max_attempts, bool) or not isinstance(self.max_attempts, int):
            raise TypeError("max_attempts must be a positive integer")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.max_attempts > 5:
            raise ValueError("max_attempts cannot exceed 5")

        if isinstance(self.delay_seconds, bool) or not isinstance(self.delay_seconds, (int, float)):
            raise TypeError("delay_seconds must be numeric")
        if self.delay_seconds < 0.0:
            raise ValueError("delay_seconds must be non-negative")

        if not isinstance(self.retryable_exceptions, tuple) or not all(
            isinstance(exc, type) and issubclass(exc, Exception) for exc in self.retryable_exceptions
        ):
            raise TypeError("retryable_exceptions must be a tuple of Exception classes")


@dataclass(frozen=True)
class AutomationConfig:
    tool_timeout: float = 30.0
    max_output_size: int = 20_000
    max_task_steps: int = MAX_TASK_STEPS
    require_approval_for_sensitive_tools: bool = True
    db_path: Path | None = None
    retry_policy: RetryPolicy | None = None

    def __post_init__(self):
        if isinstance(self.tool_timeout, bool) or not isinstance(self.tool_timeout, (int, float)):
            raise TypeError("tool_timeout must be a positive number")
        if self.tool_timeout <= 0:
            raise ValueError("tool_timeout must be greater than 0")

        if isinstance(self.max_output_size, bool) or not isinstance(self.max_output_size, int):
            raise TypeError("max_output_size must be a positive integer")
        if self.max_output_size <= 0:
            raise ValueError("max_output_size must be greater than 0")

        if isinstance(self.max_task_steps, bool) or not isinstance(self.max_task_steps, int):
            raise TypeError("max_task_steps must be a positive integer")
        if self.max_task_steps <= 0:
            raise ValueError("max_task_steps must be greater than 0")
        if self.max_task_steps > MAX_TASK_STEPS:
            raise ValueError(f"max_task_steps cannot exceed supported limit of {MAX_TASK_STEPS}")

        if not isinstance(self.require_approval_for_sensitive_tools, bool):
            raise TypeError("require_approval_for_sensitive_tools must be a boolean")

        if self.retry_policy is not None and not isinstance(self.retry_policy, RetryPolicy):
            raise TypeError("retry_policy must be a RetryPolicy or None")

        if self.db_path is not None:
            if isinstance(self.db_path, str):
                if not self.db_path.strip():
                    raise ValueError("db_path must not be empty")
                object.__setattr__(self, "db_path", Path(self.db_path))
            elif isinstance(self.db_path, Path):
                if not str(self.db_path).strip():
                    raise ValueError("db_path must not be empty")
            else:
                raise TypeError("db_path must be a str, Path, or None")
