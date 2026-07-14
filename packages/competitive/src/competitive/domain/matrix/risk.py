"""The Risk matrix — competitive threats, scored deterministically.

A :class:`CompetitiveRisk` is a threat the competitive landscape poses (a leader's
advantage, a ubiquitous pattern the client lacks, a platform constraint). It scores
itself from a severity × likelihood matrix. :class:`RiskMatrix` aggregates them into
an overall level.

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import EvidenceId, RiskId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Likelihood,
    Severity,
)

__all__ = ["CompetitiveRisk", "InvalidRiskError", "RiskLevel", "RiskMatrix"]


class InvalidRiskError(DesignDirectorError):
    """Raised when a competitive risk is constructed with invalid data."""

    code = "invalid_competitive_risk"
    http_status = 422


class RiskLevel(str, Enum):
    """The level a severity × likelihood score maps to."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: int) -> RiskLevel:
        """Map a 1–16 score to a level (``<=3`` LOW, ``<=7`` MEDIUM, ``<=11`` HIGH)."""
        if score <= 3:
            return cls.LOW
        if score <= 7:
            return cls.MEDIUM
        if score <= 11:
            return cls.HIGH
        return cls.CRITICAL

    @property
    def rank(self) -> int:
        return _LEVEL_RANK[self]


_LEVEL_RANK: dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


@dataclass(frozen=True, slots=True)
class CompetitiveRisk:
    """A single competitive threat, with a deterministic score and level.

    Attributes:
        id: Risk identity.
        dimension: The dimension the threat concerns.
        description: What the threat is.
        severity: How damaging.
        likelihood: How probable.
        threat_source: The competitor/pattern posing the threat.
        mitigation: The recommended mitigation.
        evidence_ids: Knowledge citations supporting the risk, if any.
    """

    id: RiskId
    dimension: CompetitorDimension
    description: str
    severity: Severity
    likelihood: Likelihood
    threat_source: str = ""
    mitigation: str = ""
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidRiskError("CompetitiveRisk.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def score(self) -> int:
        return int(self.severity) * int(self.likelihood)

    @property
    def level(self) -> RiskLevel:
        return RiskLevel.from_score(self.score)


@dataclass(frozen=True, slots=True)
class RiskMatrix:
    """The aggregate competitive-risk picture."""

    risks: tuple[CompetitiveRisk, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "risks", tuple(self.risks))

    def __len__(self) -> int:
        return len(self.risks)

    @property
    def overall_level(self) -> RiskLevel:
        """The highest risk level present (LOW if none)."""
        if not self.risks:
            return RiskLevel.LOW
        return max((r.level for r in self.risks), key=lambda lvl: lvl.rank)

    @property
    def has_critical(self) -> bool:
        return any(r.level is RiskLevel.CRITICAL for r in self.risks)

    def by_level(self, level: RiskLevel) -> tuple[CompetitiveRisk, ...]:
        return tuple(r for r in self.risks if r.level is level)
