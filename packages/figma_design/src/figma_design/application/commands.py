"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from figma_design.application.request import FigmaDesignRequest
from figma_design.domain.shared.ids import FigmaDesignModelLineageId

__all__ = ["BuildFigmaDesign"]


@dataclass(frozen=True, slots=True)
class BuildFigmaDesign:
    """Build a Figma design model for a request.

    Attributes:
        request: What to model.
        lineage_id: The model lineage to append a new version to; ``None`` starts a fresh lineage.
    """

    request: FigmaDesignRequest
    lineage_id: FigmaDesignModelLineageId | None = None
