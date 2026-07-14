"""Brand copy guidelines — how the brand writes (never the copy itself).

:class:`BrandCopyGuidelines` states the principles for headlines, CTAs, and microcopy,
and the reading level to write to — the rules a copywriter (human or machine) follows.
It writes no headlines, buttons, or body copy. Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["BrandCopyGuidelines", "InvalidCopyError"]


class InvalidCopyError(DesignDirectorError):
    """Raised when copy guidelines are constructed with invalid data."""

    code = "invalid_copy_guidelines"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandCopyGuidelines:
    """The cited rules for how the brand writes.

    Attributes:
        headline_principles: How headlines should work.
        cta_style: How calls-to-action should read.
        microcopy_stance: How microcopy (labels, errors, hints) should read.
        reading_level: The target reading level.
        do: Copy do's.
        dont: Copy don'ts.
        evidence_ids: The evidence supporting it.
    """

    headline_principles: tuple[str, ...] = ()
    cta_style: str = ""
    microcopy_stance: str = ""
    reading_level: str = ""
    do: tuple[str, ...] = ()
    dont: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "headline_principles", tuple(self.headline_principles))
        object.__setattr__(self, "do", tuple(self.do))
        object.__setattr__(self, "dont", tuple(self.dont))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
