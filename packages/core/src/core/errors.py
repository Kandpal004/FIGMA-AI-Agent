"""Structured error hierarchy.

A single base (`DesignDirectorError`) lets the API layer translate any internal
failure into a consistent HTTP problem response, while specific subclasses let
the orchestrator branch on *why* something failed (a transient LLM hiccup is
retryable; an invalid workflow transition is not).

Design rules:
* Every error carries a machine-readable `code` (stable string) and an
  optional `details` mapping for structured context.
* Never raise bare `Exception` inside the platform — pick or add a subclass here.
"""

from __future__ import annotations

from typing import Any


class DesignDirectorError(Exception):
    """Base class for all platform errors.

    `code` is a stable, snake_case identifier safe to expose to clients and to
    branch on. `details` holds structured, non-sensitive context.
    """

    code: str = "internal_error"
    http_status: int = 500

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        self.details: dict[str, Any] = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize into an RFC-7807-ish problem payload."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# --------------------------------------------------------------------------- #
# Configuration & wiring
# --------------------------------------------------------------------------- #
class ConfigurationError(DesignDirectorError):
    """A required setting is missing, malformed, or contradictory."""

    code = "configuration_error"
    http_status = 500


# --------------------------------------------------------------------------- #
# Agents
# --------------------------------------------------------------------------- #
class AgentError(DesignDirectorError):
    """Base for failures originating inside an agent's `run`."""

    code = "agent_error"
    http_status = 502


class AgentTimeoutError(AgentError):
    """An agent exceeded its allotted execution time. Retryable."""

    code = "agent_timeout"


class AgentValidationError(AgentError):
    """An agent produced output that failed contract validation. Not retryable
    without changing the input or the agent."""

    code = "agent_validation_error"
    http_status = 422


# --------------------------------------------------------------------------- #
# LLM
# --------------------------------------------------------------------------- #
class LLMError(DesignDirectorError):
    """Base for failures talking to the language model provider."""

    code = "llm_error"
    http_status = 502


class LLMRateLimitError(LLMError):
    """Provider rate-limited us. Retryable with backoff."""

    code = "llm_rate_limited"
    http_status = 429


class LLMTimeoutError(LLMError):
    """The LLM request timed out. Retryable."""

    code = "llm_timeout"


# --------------------------------------------------------------------------- #
# Workflow / orchestration
# --------------------------------------------------------------------------- #
class WorkflowError(DesignDirectorError):
    """Base for orchestration/state-machine failures."""

    code = "workflow_error"
    http_status = 409


class InvalidTransitionError(WorkflowError):
    """A transition was requested that the state machine does not permit from
    the run's current state."""

    code = "invalid_transition"


class UnknownAgentError(WorkflowError):
    """The mediator was asked to route to an agent not present in the registry."""

    code = "unknown_agent"
    http_status = 500


# --------------------------------------------------------------------------- #
# Tools (MCP / Figma / commerce adapters)
# --------------------------------------------------------------------------- #
class ToolError(DesignDirectorError):
    """A downstream tool/integration failed."""

    code = "tool_error"
    http_status = 502


class NotFoundError(DesignDirectorError):
    """A requested resource (run, tenant, section) does not exist."""

    code = "not_found"
    http_status = 404
