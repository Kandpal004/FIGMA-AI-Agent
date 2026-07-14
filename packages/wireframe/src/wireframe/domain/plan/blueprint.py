"""The PlanBlueprint — the set of page plans that constitute a wireframe plan.

A :class:`PlanBlueprint` is the immutable collection of :class:`PagePlan` s, one per page
type in scope. It is the structural core of the wireframe plan: the pages, their ordered
sections, and the section web across them. Uniqueness is enforced per page type (a plan
defines each page once); :class:`PageType.CMS` may repeat (distinguished by purpose).

Pure domain: standard library, the shared-kernel error base, wireframe ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.page.page_plan import PagePlan
from wireframe.domain.section.section_plan import SectionPlan
from wireframe.domain.shared.ids import SectionId, WFEvidenceId
from wireframe.domain.shared.value_objects import PageType

__all__ = ["InvalidPlanBlueprintError", "PlanBlueprint"]


class InvalidPlanBlueprintError(DesignDirectorError):
    """Raised when a plan blueprint is constructed with invalid data."""

    code = "invalid_wireframe_blueprint"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PlanBlueprint:
    """The cited set of page plans that make up the wireframe plan."""

    pages: tuple[PagePlan, ...] = ()

    def __post_init__(self) -> None:
        pages = tuple(self.pages)
        seen_pages: set[PageType] = set()
        seen_sections: set[SectionId] = set()
        for page in pages:
            if page.page_type is not PageType.CMS:
                if page.page_type in seen_pages:
                    raise InvalidPlanBlueprintError(
                        "Duplicate page plan for the same page type.",
                        details={"page_type": page.page_type.value},
                    )
                seen_pages.add(page.page_type)
            for section in page.sections:
                if section.id in seen_sections:
                    raise InvalidPlanBlueprintError(
                        "Section id repeated across page plans.",
                        details={"section_id": str(section.id)},
                    )
                seen_sections.add(section.id)
        object.__setattr__(self, "pages", pages)

    @classmethod
    def of(cls, pages: Iterable[PagePlan]) -> PlanBlueprint:
        return cls(pages=tuple(pages))

    def __len__(self) -> int:
        return len(self.pages)

    def __iter__(self):
        return iter(self.pages)

    def has(self, page_type: PageType) -> bool:
        return any(p.page_type is page_type for p in self.pages)

    def get(self, page_type: PageType) -> PagePlan | None:
        return next((p for p in self.pages if p.page_type is page_type), None)

    def page_types(self) -> frozenset[PageType]:
        return frozenset(p.page_type for p in self.pages)

    def sections(self) -> tuple[SectionPlan, ...]:
        return tuple(s for p in self.pages for s in p.sections)

    def section_ids(self) -> frozenset[SectionId]:
        return frozenset(s.id for p in self.pages for s in p.sections)

    def get_section(self, section_id: SectionId) -> SectionPlan | None:
        return next(
            (s for p in self.pages for s in p.sections if s.id == section_id), None
        )

    def section_count(self) -> int:
        return sum(len(p.sections) for p in self.pages)

    def evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        return tuple(eid for p in self.pages for eid in p.all_evidence_ids())
