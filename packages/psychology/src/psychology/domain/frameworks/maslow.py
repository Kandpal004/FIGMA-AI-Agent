"""Maslow's hierarchy — which needs the purchase ultimately serves.

A :class:`MaslowMapping` names the dominant need the offer speaks to and the other
active needs, cited. Locating the purchase in the hierarchy tells messaging which need
to lead with (safety for a high-risk buy, esteem for a status buy, and so on).

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import MaslowNeed

__all__ = ["InvalidMaslowError", "MaslowMapping"]


class InvalidMaslowError(DesignDirectorError):
    """Raised when a Maslow mapping is constructed with invalid data."""

    code = "invalid_maslow_mapping"
    http_status = 422


@dataclass(frozen=True, slots=True)
class MaslowMapping:
    """The cited placement of the purchase in Maslow's hierarchy.

    Attributes:
        dominant_need: The need the offer most speaks to.
        active_needs: The other needs in play.
        rationale: Why the purchase serves this need.
        evidence_ids: The evidence supporting it.
    """

    dominant_need: MaslowNeed
    active_needs: tuple[MaslowNeed, ...] = ()
    rationale: str = ""
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        deduped: list[MaslowNeed] = []
        for need in self.active_needs:
            if need is not self.dominant_need and need not in deduped:
                deduped.append(need)
        object.__setattr__(self, "active_needs", tuple(deduped))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
