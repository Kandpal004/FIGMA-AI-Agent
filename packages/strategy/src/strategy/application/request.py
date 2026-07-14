"""The Strategy Request — the engine's typed input contract.

A :class:`StrategyRequest` carries the *given* context of an engagement — the brand,
the project, and the raw goals. The engine gathers the evidence itself through its
input ports; the caller supplies only what it knows.

Pure application: standard library and the domain context models.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.context.context import BrandContext, GoalContext, ProjectContext

__all__ = ["InvalidStrategyRequestError", "StrategyRequest"]


class InvalidStrategyRequestError(DesignDirectorError):
    """Raised when a strategy request is constructed with invalid data."""

    code = "invalid_strategy_request"
    http_status = 422


@dataclass(frozen=True, slots=True)
class StrategyRequest:
    """What the Business Strategy Engine is asked to produce a strategy for.

    Attributes:
        brand: The brand context.
        project: The project context.
        goals: The raw business and user goals.
    """

    brand: BrandContext
    project: ProjectContext
    goals: GoalContext = GoalContext()

    @property
    def project_id(self) -> str:
        return self.project.project_id
