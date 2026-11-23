"""Safe subprocess adapter for executing Hermes CLI commands."""

import subprocess

from src.hermes.config import HermesConfig
from src.hermes.errors import (
    HermesExecutionError,
    HermesTimeoutError,
    HermesUnavailableError,
    InvalidRequestError,
)


class HermesCLIAdapter:
    def __init__(self, config: HermesConfig | None = None):
        self.config = config or HermesConfig()

    def invoke(self, query: str, options: dict | None = None) -> str:
        """Invoke Hermes in single-query oneshot mode with bounded resources."""
        if not self.config.enabled:
            raise HermesUnavailableError("Hermes integration is disabled")

        if not isinstance(query, str) or not query.strip():
            raise InvalidRequestError("Query must be a non-empty string")

        if len(query) > self.config.max_request_size:
            raise InvalidRequestError(
                f"Query exceeds maximum allowed length of {self.config.max_request_size} characters"
            )

        cmd = [
            self.config.executable_path,
            "chat",
            "-q",
            query,
            "--oneshot",
            "-Q",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                shell=False,
            )
        except FileNotFoundError as err:
            raise HermesUnavailableError(
                f"Executable not found: {self.config.executable_path}"
            ) from err
        except subprocess.TimeoutExpired as err:
            raise HermesTimeoutError(
                f"Hermes command timed out after {self.config.timeout} seconds"
            ) from err
        except Exception as err:
            raise HermesExecutionError(f"Subprocess execution failed: {err}") from err

        if result.returncode != 0:
            error_msg = (
                result.stderr.strip()
                or f"Hermes exited with returncode {result.returncode}"
            )
            raise HermesExecutionError(error_msg)

        output = result.stdout
        if len(output) > self.config.max_output_size:
            output = output[: self.config.max_output_size] + "\n... [TRUNCATED]"

        return output
