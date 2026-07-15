"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from component_intelligence.application.request import ComponentIntelligenceRequest
from component_intelligence.domain.shared.ids import ComponentSpecLineageId

__all__ = ["BuildComposition"]


@dataclass(frozen=True, slots=True)
class BuildComposition:
    """Build a component-composition specification for a request.

    Attributes:
        request: What to compose.
        lineage_id: The specification lineage to append a new version to; ``None`` starts a
            fresh lineage.
    """

    request: ComponentIntelligenceRequest
    lineage_id: ComponentSpecLineageId | None = None
