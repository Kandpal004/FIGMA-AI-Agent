"""Placement rules — which component belongs on which page, and where.

A :class:`PlacementRule` binds a component to a page, a region on that page, and an order — the
authoritative answer to "which component belongs on which page". The :class:`PlacementRuleSet`
is the immutable collection, queryable by page. It is also what the coherence invariant reads
to detect two conflicting components co-placed on the same page.

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEvidenceId, RuleId
from component_intelligence.domain.shared.value_objects import ComponentType, PageType, PlacementRegion

__all__ = ["InvalidPlacementError", "PlacementRule", "PlacementRuleSet"]


class InvalidPlacementError(DesignDirectorError):
    """Raised when a placement rule or set is constructed with invalid data."""

    code = "invalid_component_intelligence_placement"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PlacementRule:
    """Where a component is placed on a page.

    Attributes:
        id: Rule identity.
        component: The component being placed.
        page: The page it is placed on.
        region: The region on the page.
        order: Its order within the region (0-based).
        evidence_ids: The evidence grounding the placement.
    """

    id: RuleId
    component: ComponentType
    page: PageType
    region: PlacementRegion
    order: int = 0
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.order, int) or self.order < 0:
            raise InvalidPlacementError(
                "PlacementRule.order must be a non-negative int.", details={"order": self.order}
            )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class PlacementRuleSet:
    """The immutable set of placement rules."""

    rules: tuple[PlacementRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[PlacementRule]) -> PlacementRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def for_page(self, page: PageType) -> tuple[PlacementRule, ...]:
        return tuple(sorted(
            (r for r in self.rules if r.page is page), key=lambda r: (r.region.value, r.order)
        ))

    def for_component(self, component: ComponentType) -> tuple[PlacementRule, ...]:
        return tuple(r for r in self.rules if r.component is component)

    def components_on(self, page: PageType) -> frozenset[ComponentType]:
        return frozenset(r.component for r in self.rules if r.page is page)

    def pages(self) -> frozenset[PageType]:
        return frozenset(r.page for r in self.rules)

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.all_evidence_ids())
