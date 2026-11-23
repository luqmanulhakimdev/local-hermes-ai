"""Configuration model for Hermes agent integration."""

from dataclasses import dataclass

from src.hermes.errors import HermesConfigError

DEFAULT_HERMES_EXECUTABLE = "/home/luqmanul/.local/bin/hermes"
DEFAULT_HERMES_TIMEOUT = 60
DEFAULT_HERMES_MAX_OUTPUT = 20_000
DEFAULT_HERMES_MAX_REQUEST = 10_000
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:4b-instruct-2507-q4_K_M"


@dataclass(frozen=True)
class HermesConfig:
    enabled: bool = True
    executable_path: str = DEFAULT_HERMES_EXECUTABLE
    timeout: int = DEFAULT_HERMES_TIMEOUT
    max_output_size: int = DEFAULT_HERMES_MAX_OUTPUT
    max_request_size: int = DEFAULT_HERMES_MAX_REQUEST
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    ollama_model: str = DEFAULT_OLLAMA_MODEL

    def __post_init__(self):
        if not isinstance(self.enabled, bool):
            raise HermesConfigError("enabled must be a boolean")

        if not isinstance(self.executable_path, str) or not self.executable_path.strip():
            raise HermesConfigError("executable_path must be a non-empty string")

        if (
            not isinstance(self.timeout, int)
            or isinstance(self.timeout, bool)
            or self.timeout <= 0
        ):
            raise HermesConfigError("timeout must be a positive integer")

        if (
            not isinstance(self.max_output_size, int)
            or isinstance(self.max_output_size, bool)
            or self.max_output_size <= 0
        ):
            raise HermesConfigError("max_output_size must be a positive integer")

        if (
            not isinstance(self.max_request_size, int)
            or isinstance(self.max_request_size, bool)
            or self.max_request_size <= 0
        ):
            raise HermesConfigError("max_request_size must be a positive integer")

        if not isinstance(self.ollama_base_url, str) or not (
            self.ollama_base_url.startswith("http://")
            or self.ollama_base_url.startswith("https://")
        ):
            raise HermesConfigError(
                "ollama_base_url must be a valid http/https URL string"
            )

        if not isinstance(self.ollama_model, str) or not self.ollama_model.strip():
            raise HermesConfigError("ollama_model must be a non-empty string")
