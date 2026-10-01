"""Exceptions for Model Gateway."""

from __future__ import annotations


class GatewayError(Exception):
    """Base class for all Model Gateway exceptions."""


class ContractNotFoundError(GatewayError):
    """Raised when a ModelTaskContract is not registered or found."""


class NoQualifiedEndpointError(GatewayError):
    """Raised when no endpoint passes qualification, health, or policy gates."""


class ResidencyFailClosedError(NoQualifiedEndpointError):
    """Raised when IN_ONLY residency policy cannot be satisfied (fails closed)."""


class BudgetExhaustedError(GatewayError):
    """Raised when request or task cost budget has been exhausted."""


class SchemaValidationError(GatewayError):
    """Raised when model output fails contract schema validation and cannot be repaired."""


class AdapterInvocationError(GatewayError):
    """Raised when provider API call encounters an unrecoverable failure."""
