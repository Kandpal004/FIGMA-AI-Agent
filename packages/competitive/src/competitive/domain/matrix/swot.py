"""The SWOT matrix — the client's position, evidenced.

Each :class:`SWOTItem` is an evidenced claim in one of the four quadrants,
derived deterministically from the benchmark and the detected patterns (strengths
where the client leads, weaknesses where it trails, opportunities in category
whitespace, threats from category leaders). :class:`SWOTMatrix` groups them.

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import EvidenceId
from competitive.domain.shared.value_objects import CompetitorDimension, Confidence

__all__ = ["InvalidSwotError", "SWOTItem", "SWOTMatrix", "SWOTQuadrant"]


class InvalidSwotError(DesignDirectorError):
    """Raised when a SWOT item is constructed with invalid data."""

    code = "invalid_swot"
    http_status = 422


class SWOTQuadrant(str, Enum):
    """The four SWOT quadrants."""

    STRENGTH = "strength"
    WEAKNESS = "weakness"
    OPPORTUNITY = "opportunity"
    THREAT = "threat"


@dataclass(frozen=True, slots=True)
class SWOTItem:
    """One evidenced item in a SWOT quadrant.

    Attributes:
        quadrant: Which quadrant it belongs to.
        statement: The claim.
        confidence: Confidence in the claim.
        dimension: The dimension it concerns, if any.
        evidence_ids: Knowledge citations backing it.
    """

    quadrant: SWOTQuadrant
    statement: str
    confidence: Confidence
    dimension: CompetitorDimension | None = None
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidSwotError("SWOTItem.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class SWOTMatrix:
    """The client's SWOT, grouped by quadrant."""

    items: tuple[SWOTItem, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))

    def _of(self, quadrant: SWOTQuadrant) -> tuple[SWOTItem, ...]:
        return tuple(i for i in self.items if i.quadrant is quadrant)

    def strengths(self) -> tuple[SWOTItem, ...]:
        return self._of(SWOTQuadrant.STRENGTH)

    def weaknesses(self) -> tuple[SWOTItem, ...]:
        return self._of(SWOTQuadrant.WEAKNESS)

    def opportunities(self) -> tuple[SWOTItem, ...]:
        return self._of(SWOTQuadrant.OPPORTUNITY)

    def threats(self) -> tuple[SWOTItem, ...]:
        return self._of(SWOTQuadrant.THREAT)
