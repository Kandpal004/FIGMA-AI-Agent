"""Friction analysis — where the experience slows or blocks the user.

A :class:`FrictionPoint` locates one point of experience friction, its kind and severity,
the journey phase it occurs in, and the remedy. The :class:`FrictionAnalysis` is the
immutable collection. These translate the psychology model's friction into experience-level
friction the design must remove. Cited.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import FrictionPointId, UXEvidenceId
from ux.domain.shared.value_objects import (
    FrictionKind,
    JourneyPhase,
    PageKind,
    Severity,
)

__all__ = ["FrictionAnalysis", "FrictionPoint", "InvalidFrictionError"]


class InvalidFrictionError(DesignDirectorError):
    """Raised when a friction point is constructed with invalid data."""

    code = "invalid_friction_point"
    http_status = 422


@dataclass(frozen=True, slots=True)
class FrictionPoint:
    """One cited point of experience friction.

    Attributes:
        id: Friction point identity.
        location: Where the friction occurs (description).
        kind: The kind of friction.
        severity: How much it slows/blocks the user.
        phase: The journey phase it occurs in.
        page: The page it occurs on, if any.
        remedy: The strategy to remove it.
        evidence_ids: The evidence supporting it.
    """

    id: FrictionPointId
    location: str
    kind: FrictionKind
    severity: Severity
    phase: JourneyPhase
    page: PageKind | None = None
    remedy: str = ""
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.location or not self.location.strip():
            raise InvalidFrictionError("FrictionPoint.location must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class FrictionAnalysis:
    """An immutable analysis of the experience's friction points."""

    points: tuple[FrictionPoint, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))

    @classmethod
    def of(cls, points: Iterable[FrictionPoint]) -> FrictionAnalysis:
        return cls(points=tuple(points))

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self):
        return iter(self.points)

    def by_severity(self) -> tuple[FrictionPoint, ...]:
        return tuple(sorted(self.points, key=lambda p: int(p.severity), reverse=True))

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for p in self.points for eid in p.evidence_ids)
