"""The Structure strategy — which sections a page should have, and their fate.

Answers the "what sections should exist / which are optional / which should be
removed" questions. A :class:`SectionRecommendation` is a cited verdict on one
section — required, optional, or removed — with a rationale, an ordering, and (like
every strategy point) at least one piece of evidence. :class:`StructureStrategy`
collects the recommendations for a page.

The engine never invents sections it cannot justify: each recommendation carries
evidence, and a section it wants to *remove* is justified just as rigorously as one
it wants to keep.

Pure domain: standard library, the shared-kernel error base, and reasoning ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.errors import DesignDirectorError

from reasoning.domain.shared.ids import EvidenceId

__all__ = [
    "InvalidStructureError",
    "SectionRecommendation",
    "SectionStatus",
    "StructureStrategy",
]


class InvalidStructureError(DesignDirectorError):
    """Raised when a section recommendation or structure strategy is invalid."""

    code = "invalid_structure"
    http_status = 422


class SectionStatus(str, Enum):
    """The engine's verdict on a section.

    * ``REQUIRED`` — must be present.
    * ``OPTIONAL`` — may be included; include if resources allow.
    * ``REMOVED``  — should not be present (actively recommended against).
    """

    REQUIRED = "required"
    OPTIONAL = "optional"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class SectionRecommendation:
    """A cited verdict on one page section.

    Attributes:
        name: The section slug (e.g. ``"hero"``, ``"testimonials"``).
        status: The verdict.
        rationale: Why this verdict was reached.
        evidence_ids: The evidence backing it (must be non-empty).
        confidence: Confidence in the verdict, in ``[0, 1]``.
        order: The section's position in the page (``>= 0``); ordering hint only.
    """

    name: str
    status: SectionStatus
    rationale: str
    evidence_ids: tuple[EvidenceId, ...]
    confidence: float
    order: int = 0

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidStructureError("SectionRecommendation.name must be non-empty.")
        if not self.rationale or not self.rationale.strip():
            raise InvalidStructureError("SectionRecommendation.rationale must be non-empty.")
        normalized = tuple(self.evidence_ids)
        if not normalized:
            raise InvalidStructureError(
                "A section recommendation must cite at least one piece of evidence.",
                details={"section": self.name},
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidStructureError(
                "SectionRecommendation.confidence must be within [0, 1].",
                details={"confidence": self.confidence},
            )
        if self.order < 0:
            raise InvalidStructureError("SectionRecommendation.order must be >= 0.")
        object.__setattr__(self, "evidence_ids", normalized)

    @property
    def is_required(self) -> bool:
        return self.status is SectionStatus.REQUIRED


@dataclass(frozen=True, slots=True)
class StructureStrategy:
    """The recommended section structure for a page.

    Attributes:
        sections: The section recommendations (unique by name).
    """

    sections: tuple[SectionRecommendation, ...] = ()

    def __post_init__(self) -> None:
        normalized = tuple(self.sections)
        seen: set[str] = set()
        for section in normalized:
            if section.name in seen:
                raise InvalidStructureError(
                    "Duplicate section name in structure strategy.",
                    details={"section": section.name},
                )
            seen.add(section.name)
        object.__setattr__(self, "sections", normalized)

    def _of_status(self, status: SectionStatus) -> tuple[SectionRecommendation, ...]:
        return tuple(s for s in self.sections if s.status is status)

    def required(self) -> tuple[SectionRecommendation, ...]:
        """Sections that must be present, in page order."""
        return tuple(sorted(self._of_status(SectionStatus.REQUIRED), key=lambda s: s.order))

    def optional(self) -> tuple[SectionRecommendation, ...]:
        """Sections that may be included."""
        return self._of_status(SectionStatus.OPTIONAL)

    def removed(self) -> tuple[SectionRecommendation, ...]:
        """Sections recommended against."""
        return self._of_status(SectionStatus.REMOVED)

    def evidence_ids(self) -> tuple[EvidenceId, ...]:
        """Every evidence id referenced by the structure, de-duplicated."""
        seen: list[EvidenceId] = []
        for section in self.sections:
            for eid in section.evidence_ids:
                if eid not in seen:
                    seen.append(eid)
        return tuple(seen)
