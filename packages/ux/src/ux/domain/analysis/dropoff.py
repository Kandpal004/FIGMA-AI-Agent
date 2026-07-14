"""Drop-off analysis — where the user is most likely to abandon.

A :class:`DropoffRisk` names one point where the user may abandon the funnel, its kind,
likelihood and impact, and the mitigation. The :class:`DropoffAnalysis` is the immutable
collection and computes the highest-risk stage. These translate the psychology model's
exit risks into funnel drop-off the design must protect against. Cited.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import (
    DropoffKind,
    Impact,
    JourneyPhase,
    Severity,
)

__all__ = ["DropoffAnalysis", "DropoffRisk", "InvalidDropoffError"]


class InvalidDropoffError(DesignDirectorError):
    """Raised when a drop-off risk is constructed with invalid data."""

    code = "invalid_dropoff_risk"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DropoffRisk:
    """One cited drop-off risk.

    Attributes:
        stage: The journey phase where abandonment is likely.
        kind: The kind of drop-off.
        likelihood: How likely abandonment is here (1–5).
        impact: How costly the abandonment is (1–5).
        mitigation: The strategy to reduce it.
        evidence_ids: The evidence supporting it.
    """

    stage: JourneyPhase
    kind: DropoffKind
    likelihood: Severity
    impact: Impact
    mitigation: str = ""
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def risk_score(self) -> int:
        """Likelihood × impact, in ``[1, 25]``."""
        return int(self.likelihood) * int(self.impact)


@dataclass(frozen=True, slots=True)
class DropoffAnalysis:
    """An immutable analysis of the funnel's drop-off risks."""

    risks: tuple[DropoffRisk, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "risks", tuple(self.risks))

    @classmethod
    def of(cls, risks: Iterable[DropoffRisk]) -> DropoffAnalysis:
        return cls(risks=tuple(risks))

    def __len__(self) -> int:
        return len(self.risks)

    def __iter__(self):
        return iter(self.risks)

    def by_risk(self) -> tuple[DropoffRisk, ...]:
        return tuple(sorted(self.risks, key=lambda r: r.risk_score, reverse=True))

    def highest_risk(self) -> DropoffRisk | None:
        return max(self.risks, key=lambda r: r.risk_score, default=None)

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for r in self.risks for eid in r.evidence_ids)
