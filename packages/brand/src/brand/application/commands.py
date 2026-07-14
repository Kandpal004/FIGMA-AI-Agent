"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from brand.application.request import BrandRequest
from brand.domain.shared.ids import BrandReportLineageId

__all__ = ["BuildBrand"]


@dataclass(frozen=True, slots=True)
class BuildBrand:
    """Build a brand strategy for a request.

    Attributes:
        request: What to build a brand for.
        lineage_id: The report lineage to append a new version to; ``None`` starts a
            fresh lineage.
    """

    request: BrandRequest
    lineage_id: BrandReportLineageId | None = None
