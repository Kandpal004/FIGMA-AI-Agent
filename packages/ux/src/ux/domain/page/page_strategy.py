"""Page strategy — the cited definition of why a page exists and what it must do.

A :class:`PageStrategy` is the atomic unit of the UX strategy: for one key page it states
the objective, the primary and secondary CTAs, the success metrics, the information and
content priority, and the UX laws that govern it. Every future screen must trace to one
of these — this is where WHY is decided, before anything decides HOW.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.page.cta import CallToAction
from ux.domain.page.objective import PageObjective, SuccessMetric
from ux.domain.page.priority import ContentPriority, InformationPriority
from ux.domain.shared.ids import PageStrategyId, UXEvidenceId
from ux.domain.shared.value_objects import CTAType, PageKind, UXLaw

__all__ = ["InvalidPageStrategyError", "PageStrategy", "PageStrategySet"]


class InvalidPageStrategyError(DesignDirectorError):
    """Raised when a page strategy is constructed with invalid data."""

    code = "invalid_page_strategy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PageStrategy:
    """The cited strategy for one key page.

    Attributes:
        id: Page strategy identity.
        page: Which page/surface this governs.
        objective: Why the page exists and what it must accomplish.
        ctas: The calls to action the page drives.
        success_metrics: How the page's success is measured.
        information_priority: The page's information priority.
        content_priority: The page's content priority.
        applicable_laws: The UX laws that most govern this page.
        evidence_ids: The evidence supporting the strategy.
    """

    id: PageStrategyId
    page: PageKind
    objective: PageObjective
    ctas: tuple[CallToAction, ...] = ()
    success_metrics: tuple[SuccessMetric, ...] = ()
    information_priority: InformationPriority = InformationPriority()
    content_priority: ContentPriority = ContentPriority()
    applicable_laws: tuple[UXLaw, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "ctas", tuple(self.ctas))
        object.__setattr__(self, "success_metrics", tuple(self.success_metrics))
        object.__setattr__(self, "applicable_laws", tuple(dict.fromkeys(self.applicable_laws)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def primary_cta(self) -> CallToAction | None:
        return next((c for c in self.ctas if c.type is CTAType.PRIMARY), None)

    def secondary_ctas(self) -> tuple[CallToAction, ...]:
        return tuple(c for c in self.ctas if c.type is not CTAType.PRIMARY)

    def all_evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return (
            *self.evidence_ids,
            *self.objective.evidence_ids,
            *(eid for c in self.ctas for eid in c.evidence_ids),
            *(eid for m in self.success_metrics for eid in m.evidence_ids),
            *self.information_priority.evidence_ids,
            *self.content_priority.evidence_ids,
        )


@dataclass(frozen=True, slots=True)
class PageStrategySet:
    """An immutable set of page strategies, one per key page."""

    pages: tuple[PageStrategy, ...] = ()

    def __post_init__(self) -> None:
        pages = tuple(self.pages)
        seen: set[PageKind] = set()
        for page in pages:
            if page.page in seen:
                raise InvalidPageStrategyError(
                    "Duplicate page strategy for the same page.",
                    details={"page": page.page.value},
                )
            seen.add(page.page)
        object.__setattr__(self, "pages", pages)

    @classmethod
    def of(cls, pages: Iterable[PageStrategy]) -> PageStrategySet:
        return cls(pages=tuple(pages))

    def __len__(self) -> int:
        return len(self.pages)

    def __iter__(self):
        return iter(self.pages)

    def get(self, page: PageKind) -> PageStrategy | None:
        return next((p for p in self.pages if p.page is page), None)

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for p in self.pages for eid in p.all_evidence_ids())
