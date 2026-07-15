"""The layout model — deterministic, breakpoint-aware region placement.

The orchestrator does not render; it computes *where things go*. A :class:`LayoutRegion` is a
named area of a page (header, main, aside, footer, or a per-section region); a
:class:`GridPlacement` positions a region on the Design-System responsive grid at a breakpoint
(column start + span + order). A :class:`LayoutModel` bundles the regions and their placements
and validates that every placement targets a declared region and fits its breakpoint's column
count.

This is placement math, not pixels: the same model drives every platform and feeds the layout
graph the orchestrator builds.

Pure domain: standard library, the shared-kernel error base, DO ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_orchestrator.domain.shared.ids import LayoutRegionId
from design_orchestrator.domain.shared.value_objects import (
    Breakpoint,
    LayoutRegionKind,
    PageType,
)

__all__ = [
    "GridPlacement",
    "InvalidLayoutError",
    "LayoutModel",
    "LayoutRegion",
]

# The Design-System grid column counts per breakpoint (aligned with P16 GridSystem defaults).
_GRID_COLUMNS: dict[Breakpoint, int] = {
    Breakpoint.MOBILE: 4,
    Breakpoint.TABLET: 8,
    Breakpoint.DESKTOP: 12,
    Breakpoint.WIDE: 12,
}


class InvalidLayoutError(DesignDirectorError):
    """Raised when the layout model is constructed with invalid data."""

    code = "invalid_design_orchestrator_layout"
    http_status = 422


@dataclass(frozen=True, slots=True)
class LayoutRegion:
    """A named area of a page.

    Attributes:
        id: Region identity.
        kind: The region kind (header / main / aside / footer / section).
        page_type: The page this region belongs to.
        parent_id: The containing region, if any (``None`` for a page-level region).
        label: A short human-readable label.
    """

    id: LayoutRegionId
    kind: LayoutRegionKind
    page_type: PageType
    parent_id: LayoutRegionId | None = None
    label: str = ""

    def __post_init__(self) -> None:
        if self.parent_id is not None and self.parent_id == self.id:
            raise InvalidLayoutError(
                "A layout region cannot be its own parent.", details={"region": str(self.id)}
            )


@dataclass(frozen=True, slots=True)
class GridPlacement:
    """A region's position on the responsive grid at one breakpoint.

    Attributes:
        region_id: The region being placed.
        breakpoint: The breakpoint band this placement applies to.
        column_start: The 1-based starting column.
        column_span: How many columns the region spans (>= 1).
        order: The 1-based vertical order among siblings at this breakpoint.
    """

    region_id: LayoutRegionId
    breakpoint: Breakpoint
    column_start: int
    column_span: int
    order: int

    def __post_init__(self) -> None:
        for name, value, low in (
            ("column_start", self.column_start, 1),
            ("column_span", self.column_span, 1),
            ("order", self.order, 1),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < low:
                raise InvalidLayoutError(
                    f"GridPlacement.{name} must be an int >= {low}.", details={name: value}
                )
        columns = _GRID_COLUMNS[self.breakpoint]
        if self.column_start + self.column_span - 1 > columns:
            raise InvalidLayoutError(
                "GridPlacement exceeds the breakpoint's column count.",
                details={
                    "breakpoint": self.breakpoint.value,
                    "columns": columns,
                    "end": self.column_start + self.column_span - 1,
                },
            )


@dataclass(frozen=True, slots=True)
class LayoutModel:
    """The regions of the plan and their grid placements.

    Attributes:
        regions: Every layout region, keyed by id.
        placements: The grid placements (each targeting a declared region).
    """

    regions: Mapping[LayoutRegionId, LayoutRegion] = field(
        default_factory=lambda: MappingProxyType({})
    )
    placements: tuple[GridPlacement, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.regions, MappingProxyType):
            object.__setattr__(self, "regions", MappingProxyType(dict(self.regions)))
        object.__setattr__(self, "placements", tuple(self.placements))
        for region in self.regions.values():
            if region.parent_id is not None and region.parent_id not in self.regions:
                raise InvalidLayoutError(
                    "A region references a parent not in the model.",
                    details={"region": str(region.id)},
                )
        for placement in self.placements:
            if placement.region_id not in self.regions:
                raise InvalidLayoutError(
                    "A grid placement targets a region not in the model.",
                    details={"region": str(placement.region_id)},
                )

    @classmethod
    def of(
        cls, regions: Iterable[LayoutRegion], placements: Iterable[GridPlacement] = ()
    ) -> LayoutModel:
        mapping: dict[LayoutRegionId, LayoutRegion] = {}
        for region in regions:
            if region.id in mapping:
                raise InvalidLayoutError(
                    "Duplicate layout region id.", details={"id": str(region.id)}
                )
            mapping[region.id] = region
        return cls(regions=MappingProxyType(mapping), placements=tuple(placements))

    def __len__(self) -> int:
        return len(self.regions)

    def regions_for(self, page_type: PageType) -> tuple[LayoutRegion, ...]:
        return tuple(r for r in self.regions.values() if r.page_type is page_type)

    def placements_for(self, region_id: LayoutRegionId) -> tuple[GridPlacement, ...]:
        return tuple(p for p in self.placements if p.region_id == region_id)
