"""The Best-Practice matrix — the repeatedly-successful patterns worth adopting.

A :class:`BestPractice` is a category pattern common enough to be treated as a
standard, with a grounded recommendation to adopt it. :class:`BestPracticeMatrix`
collects them, ranked by prevalence. Each carries Knowledge citations (no opinions).

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import EvidenceId, PatternId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Confidence,
    PatternKind,
    Prevalence,
)

__all__ = ["BestPractice", "BestPracticeMatrix", "InvalidBestPracticeError"]


class InvalidBestPracticeError(DesignDirectorError):
    """Raised when a best practice is constructed with invalid data."""

    code = "invalid_best_practice"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BestPractice:
    """A repeatedly-successful pattern recommended for adoption.

    Attributes:
        pattern_id: The pattern this best practice derives from.
        kind: The pattern category.
        dimension: The dimension it concerns.
        name: A short name.
        description: What to adopt.
        prevalence: How common it is across the category.
        confidence: Confidence in the recommendation.
        evidence_ids: Knowledge citations grounding it (must be non-empty).
    """

    pattern_id: PatternId
    kind: PatternKind
    dimension: CompetitorDimension
    name: str
    description: str
    prevalence: Prevalence
    confidence: Confidence
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidBestPracticeError("BestPractice.name must be non-empty.")
        normalized = tuple(self.evidence_ids)
        if not normalized:
            raise InvalidBestPracticeError(
                "A best practice must cite Knowledge evidence (no opinions).",
                details={"name": self.name},
            )
        object.__setattr__(self, "evidence_ids", normalized)


@dataclass(frozen=True, slots=True)
class BestPracticeMatrix:
    """The category's best practices, ranked by prevalence."""

    practices: tuple[BestPractice, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "practices", tuple(self.practices))

    def __len__(self) -> int:
        return len(self.practices)

    def ranked(self) -> tuple[BestPractice, ...]:
        """Best practices ranked by prevalence ratio, most common first."""
        return tuple(sorted(self.practices, key=lambda p: p.prevalence.ratio, reverse=True))

    def for_dimension(self, dimension: CompetitorDimension) -> tuple[BestPractice, ...]:
        return tuple(p for p in self.practices if p.dimension is dimension)
