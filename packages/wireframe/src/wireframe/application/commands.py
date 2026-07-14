"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from wireframe.application.request import WireframeRequest
from wireframe.domain.shared.ids import WireframePlanLineageId

__all__ = ["BuildWireframePlan"]


@dataclass(frozen=True, slots=True)
class BuildWireframePlan:
    """Build a wireframe execution plan for a request.

    Attributes:
        request: What to plan.
        lineage_id: The plan lineage to append a new version to; ``None`` starts a fresh
            lineage.
    """

    request: WireframeRequest
    lineage_id: WireframePlanLineageId | None = None
