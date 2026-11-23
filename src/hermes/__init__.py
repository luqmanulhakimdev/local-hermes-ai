"""Hermes Agent integration package for Local Hermes AI."""

from src.hermes.adapter import HermesCLIAdapter
from src.hermes.config import HermesConfig
from src.hermes.errors import (
    HermesConfigError,
    HermesError,
    HermesExecutionError,
    HermesTimeoutError,
    HermesUnavailableError,
    InvalidRequestError,
    OperationRejectedError,
)
from src.hermes.health import check_hermes
from src.hermes.protocol import (
    HermesRequest,
    HermesRequestStatus,
    HermesResponse,
)
from src.hermes.service import HermesService

__all__ = [
    "HermesConfig",
    "HermesError",
    "HermesConfigError",
    "HermesUnavailableError",
    "HermesTimeoutError",
    "HermesExecutionError",
    "InvalidRequestError",
    "OperationRejectedError",
    "HermesRequest",
    "HermesResponse",
    "HermesRequestStatus",
    "HermesCLIAdapter",
    "HermesService",
    "check_hermes",
]
