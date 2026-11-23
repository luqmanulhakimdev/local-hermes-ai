"""Hermes integration error hierarchy."""


class HermesError(Exception):
    """Base exception for all Hermes integration errors."""


class HermesConfigError(HermesError):
    """Raised when Hermes configuration is missing or invalid."""


class HermesUnavailableError(HermesError):
    """Raised when the Hermes CLI or runtime is unavailable or disabled."""


class HermesTimeoutError(HermesError):
    """Raised when a Hermes execution exceeds the configured timeout."""


class HermesExecutionError(HermesError):
    """Raised when a Hermes execution fails or returns an error."""


class InvalidRequestError(HermesError):
    """Raised when a Hermes request is malformed, missing fields, or exceeds limits."""


class OperationRejectedError(HermesError):
    """Raised when an operation violates security boundaries, tool allowlists, or approvals."""
