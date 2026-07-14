"""The PagePlan — a page's ordered set of section plans.

A :class:`PagePlan` binds a :class:`PageType` to the ordered sections that constitute its
wireframe plan. It is the per-page structural blueprint: the section order, which sections
are required, and the page-level goals the sections collectively serve. It carries no visual
layout — only structure and intent.

Pure domain: standard library, the shared-kernel error base, wireframe ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.section.section_plan import SectionPlan
from wireframe.domain.shared.ids import PagePlanId, SectionId, WFEvidenceId
from wireframe.domain.shared.value_objects import PageType

__all__ = ["InvalidPagePlanError", "PagePlan"]


class InvalidPagePlanError(DesignDirectorError):
    """Raised when a page plan is constructed with invalid data."""

    code = "invalid_wireframe_page_plan"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PagePlan:
    """A page and the ordered sections that make up its wireframe plan.

    Attributes:
        id: Page-plan identity.
        page_type: Which page type this plans.
        purpose: Why the page exists (grounded in the IA).
        sections: The section plans, in section order.
        evidence_ids: Evidence grounding the page-level plan.
    """

    id: PagePlanId
    page_type: PageType
    purpose: str
    sections: tuple[SectionPlan, ...] = ()
    evidence_ids: tuple[WFEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.purpose or not self.purpose.strip():
            raise InvalidPagePlanError("PagePlan.purpose must be non-empty.")
        seen: set[SectionId] = set()
        for section in self.sections:
            if section.id in seen:
                raise InvalidPagePlanError(
                    "Duplicate section id within a page plan.",
                    details={"section_id": str(section.id)},
                )
            seen.add(section.id)
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def __len__(self) -> int:
        return len(self.sections)

    def __iter__(self):
        return iter(self.sections)

    def required_sections(self) -> tuple[SectionPlan, ...]:
        return tuple(s for s in self.sections if s.is_required)

    def optional_sections(self) -> tuple[SectionPlan, ...]:
        return tuple(s for s in self.sections if not s.is_required)

    def sections_in_execution_order(self) -> tuple[SectionPlan, ...]:
        return tuple(sorted(self.sections, key=lambda s: (s.execution_order, int(s.priority) * -1)))

    def section_ids(self) -> frozenset[SectionId]:
        return frozenset(s.id for s in self.sections)

    def get(self, section_id: SectionId) -> SectionPlan | None:
        return next((s for s in self.sections if s.id == section_id), None)

    def all_evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        ids: list[WFEvidenceId] = list(self.evidence_ids)
        for section in self.sections:
            ids.extend(section.all_evidence_ids())
        return tuple(ids)
