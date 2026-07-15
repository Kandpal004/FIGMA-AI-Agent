"""Stage — Layout Construction.

Derives the :class:`LayoutModel` from the draft: one top-level region per page (the page's
declared ``region_id``) and one child SECTION region per section, each placed on the responsive
grid. Placements are deterministic — full-width at MOBILE, and at wider breakpoints either
full-width (stack/full-bleed) or split across the grid (split/grid layouts) — driven only by the
section's layout rule and its order. No pixels, only grid math.
"""

from __future__ import annotations

from design_orchestrator.application.contracts import ExecutionDraft
from design_orchestrator.domain.layout.layout import (
    GridPlacement,
    LayoutModel,
    LayoutRegion,
)
from design_orchestrator.domain.plan.section import SectionPlan
from design_orchestrator.domain.shared.ids import LayoutRegionId
from design_orchestrator.domain.shared.value_objects import Breakpoint, LayoutRegionKind

__all__ = ["LayoutBuilder"]

# Grid column counts per breakpoint (aligned with the Design System grid).
_COLUMNS: dict[Breakpoint, int] = {
    Breakpoint.MOBILE: 4,
    Breakpoint.TABLET: 8,
    Breakpoint.DESKTOP: 12,
    Breakpoint.WIDE: 12,
}


class LayoutBuilder:
    """Builds the layout model from the draft's pages and sections."""

    def build(self, draft: ExecutionDraft) -> tuple[LayoutModel, dict]:
        """Return the layout model and a section-id -> region-id index for the tree/graph."""
        regions: list[LayoutRegion] = []
        placements: list[GridPlacement] = []
        section_region: dict = {}

        for page in draft.pages:
            page_region = LayoutRegion(
                id=page.region_id,
                kind=LayoutRegionKind.MAIN,
                page_type=page.page_type,
                label=f"{page.page_type.value} main",
            )
            regions.append(page_region)
            for section in page.sections:
                region_id = LayoutRegionId.new()
                section_region[section.id] = region_id
                regions.append(
                    LayoutRegion(
                        id=region_id,
                        kind=LayoutRegionKind.SECTION,
                        page_type=page.page_type,
                        parent_id=page_region.id,
                        label=f"{section.component.value} section",
                    )
                )
                placements.extend(self._placements(section, region_id))

        return LayoutModel.of(regions, placements), section_region

    def _placements(
        self, section: SectionPlan, region_id: LayoutRegionId
    ) -> list[GridPlacement]:
        # A section region is a full-width row; its internal columns are the section's own
        # LayoutRule. Vertical order is the section order, stable across every breakpoint.
        order = int(section.order)
        return [
            GridPlacement(
                region_id=region_id,
                breakpoint=breakpoint,
                column_start=1,
                column_span=columns,
                order=order,
            )
            for breakpoint, columns in _COLUMNS.items()
        ]
