"""The page plan — an ordered sequence of section plans for one page.

A :class:`PagePlan` binds a page type to the totally-ordered list of :class:`SectionPlan` s the
orchestrator has sequenced for it, plus the layout region the page renders into. The ordering is
strict: no two sections share a position, and the sections are held in ascending order — the
deterministic section sequence a future Figma phase places top to bottom.

Pure domain: standard library, the shared-kernel error base, DO ids, the section plan, and
shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_orchestrator.domain.plan.section import SectionPlan
from design_orchestrator.domain.shared.ids import LayoutRegionId, PagePlanId
from design_orchestrator.domain.shared.value_objects import ComponentType, PageType

__all__ = ["InvalidPagePlanError", "PagePlan"]


class InvalidPagePlanError(DesignDirectorError):
    """Raised when a page plan is constructed with invalid data."""

    code = "invalid_design_orchestrator_page_plan"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PagePlan:
    """The totally-ordered sequence of sections for one page.

    Attributes:
        id: Page-plan identity.
        page_type: The page this plan is for.
        region_id: The top-level layout region this page renders into.
        sections: The section plans, held in ascending order and totally ordered.
    """

    id: PagePlanId
    page_type: PageType
    region_id: LayoutRegionId
    sections: tuple[SectionPlan, ...]

    def __post_init__(self) -> None:
        sections = tuple(self.sections)
        if not sections:
            raise InvalidPagePlanError(
                "A PagePlan must contain at least one section.",
                details={"page_type": self.page_type.value},
            )
        for section in sections:
            if section.page_type is not self.page_type:
                raise InvalidPagePlanError(
                    "A section's page_type must match its page plan.",
                    details={"page_type": self.page_type.value, "section": section.page_type.value},
                )
        orders = [int(s.order) for s in sections]
        if len(set(orders)) != len(orders):
            raise InvalidPagePlanError(
                "Section orders must be unique within a page (a total order).",
                details={"page_type": self.page_type.value, "orders": orders},
            )
        ids = [s.id for s in sections]
        if len(set(ids)) != len(ids):
            raise InvalidPagePlanError("Section ids must be unique within a page.")
        object.__setattr__(self, "sections", tuple(sorted(sections, key=lambda s: int(s.order))))

    def __len__(self) -> int:
        return len(self.sections)

    def __iter__(self):
        return iter(self.sections)

    @property
    def components(self) -> tuple[ComponentType, ...]:
        return tuple(s.component for s in self.sections)

    @property
    def evidence_ids(self) -> tuple:
        return tuple(eid for s in self.sections for eid in s.evidence_ids)
