"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from design_orchestrator.application.request import OrchestrationRequest
from design_orchestrator.domain.shared.ids import DesignExecutionPlanLineageId

__all__ = ["BuildExecutionPlan"]


@dataclass(frozen=True, slots=True)
class BuildExecutionPlan:
    """Build a design-execution plan for a request.

    Attributes:
        request: What to plan.
        lineage_id: The plan lineage to append a new version to; ``None`` starts a fresh lineage.
    """

    request: OrchestrationRequest
    lineage_id: DesignExecutionPlanLineageId | None = None
