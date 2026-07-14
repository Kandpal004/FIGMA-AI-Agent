"""The Site Map — the set of page blueprints that constitute the experience.

A :class:`SiteMap` is the immutable collection of :class:`PageBlueprint` s, partitioned into
required and optional pages. It is the structural blueprint every wireframe originates from.
Uniqueness is enforced per page type, except :class:`PageType.CUSTOM_CMS`, which may repeat
(distinguished by slug intent).

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.page.page_blueprint import PageBlueprint
from ia.domain.shared.ids import IAEvidenceId
from ia.domain.shared.value_objects import PageType

__all__ = ["InvalidSiteMapError", "SiteMap"]


class InvalidSiteMapError(DesignDirectorError):
    """Raised when a site map is constructed with invalid data (duplicate page)."""

    code = "invalid_sitemap"
    http_status = 422


@dataclass(frozen=True, slots=True)
class SiteMap:
    """The cited set of page blueprints, required and optional."""

    pages: tuple[PageBlueprint, ...] = ()

    def __post_init__(self) -> None:
        pages = tuple(self.pages)
        seen: set[PageType] = set()
        for page in pages:
            if page.page_type is PageType.CUSTOM_CMS:
                continue
            if page.page_type in seen:
                raise InvalidSiteMapError(
                    "Duplicate page blueprint for the same page type.",
                    details={"page_type": page.page_type.value},
                )
            seen.add(page.page_type)
        object.__setattr__(self, "pages", pages)

    @classmethod
    def of(cls, pages: Iterable[PageBlueprint]) -> SiteMap:
        return cls(pages=tuple(pages))

    def __len__(self) -> int:
        return len(self.pages)

    def __iter__(self):
        return iter(self.pages)

    def required(self) -> tuple[PageBlueprint, ...]:
        return tuple(p for p in self.pages if p.is_required)

    def optional(self) -> tuple[PageBlueprint, ...]:
        return tuple(p for p in self.pages if not p.is_required)

    def has(self, page_type: PageType) -> bool:
        return any(p.page_type is page_type for p in self.pages)

    def get(self, page_type: PageType) -> PageBlueprint | None:
        return next((p for p in self.pages if p.page_type is page_type), None)

    def page_types(self) -> frozenset[PageType]:
        return frozenset(p.page_type for p in self.pages)

    def evidence_ids(self) -> tuple[IAEvidenceId, ...]:
        return tuple(eid for p in self.pages for eid in p.all_evidence_ids())
