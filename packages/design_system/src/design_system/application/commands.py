"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from design_system.application.request import DesignSystemRequest
from design_system.domain.shared.ids import DesignSystemSpecLineageId

__all__ = ["BuildDesignSystem"]


@dataclass(frozen=True, slots=True)
class BuildDesignSystem:
    """Build a design-system specification for a request.

    Attributes:
        request: What to specify.
        lineage_id: The specification lineage to append a new version to; ``None`` starts a fresh
            lineage.
    """

    request: DesignSystemRequest
    lineage_id: DesignSystemSpecLineageId | None = None
