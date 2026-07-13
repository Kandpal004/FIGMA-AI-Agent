"""The Risk model — deterministically derived strategic risks.

Risks are not guessed; they are *derived* from the strategy: a decision that
contradicts another, a platform constraint that threatens a choice, a decision
resting on thin evidence. A :class:`Risk` scores itself from a calibrated
severity × likelihood matrix (deterministic), and a :class:`RiskAssessment`
aggregates the risks into an overall level.

Pure domain: standard library, the shared-kernel error base, reasoning ids, and
the shared severity/likelihood scales.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.errors import DesignDirectorError

from reasoning.domain.shared.ids import DecisionNodeId, EvidenceId, RiskId
from reasoning.domain.shared.value_objects import Likelihood, Severity

__all__ = [
    "InvalidRiskError",
    "Risk",
    "RiskAssessment",
    "RiskCategory",
    "RiskLevel",
]


class InvalidRiskError(DesignDirectorError):
    """Raised when a risk is constructed with invalid data."""

    code = "invalid_risk"
    http_status = 422


class RiskCategory(str, Enum):
    """The area a risk threatens."""

    BRAND = "brand"
    CONVERSION = "conversion"
    ACCESSIBILITY = "accessibility"
    PLATFORM = "platform"
    TECHNICAL = "technical"
    UX = "ux"
    BUSINESS = "business"


class RiskLevel(str, Enum):
    """The overall level a risk score maps to."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: int) -> RiskLevel:
        """Map a severity × likelihood score (1–16) to a level.

        Thresholds: ``<= 3`` LOW, ``<= 7`` MEDIUM, ``<= 11`` HIGH, else CRITICAL.
        """
        if score <= 3:
            return cls.LOW
        if score <= 7:
            return cls.MEDIUM
        if score <= 11:
            return cls.HIGH
        return cls.CRITICAL

    @property
    def rank(self) -> int:
        """A numeric rank for comparison (LOW=0 … CRITICAL=3)."""
        return _LEVEL_RANK[self]


_LEVEL_RANK: dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


@dataclass(frozen=True, slots=True)
class Risk:
    """A single identified risk with a deterministic score and level.

    Attributes:
        id: Risk identity.
        category: The area threatened.
        description: What the risk is.
        severity: How damaging if it materializes.
        likelihood: How probable.
        threatens: The decisions this risk endangers.
        mitigation: The recommended mitigation.
        evidence_ids: Evidence supporting the risk's existence, if any.
    """

    id: RiskId
    category: RiskCategory
    description: str
    severity: Severity
    likelihood: Likelihood
    threatens: tuple[DecisionNodeId, ...] = ()
    mitigation: str = ""
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidRiskError("Risk.description must be non-empty.")
        object.__setattr__(self, "threatens", tuple(self.threatens))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def score(self) -> int:
        """The severity × likelihood score (1–16)."""
        return int(self.severity) * int(self.likelihood)

    @property
    def level(self) -> RiskLevel:
        """The level this risk's score maps to."""
        return RiskLevel.from_score(self.score)


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """The aggregate risk picture for a strategy.

    Attributes:
        risks: The identified risks.
    """

    risks: tuple[Risk, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "risks", tuple(self.risks))

    def __len__(self) -> int:
        return len(self.risks)

    @property
    def overall_level(self) -> RiskLevel:
        """The highest risk level present (LOW if there are no risks)."""
        if not self.risks:
            return RiskLevel.LOW
        return max((r.level for r in self.risks), key=lambda lvl: lvl.rank)

    def by_category(self, category: RiskCategory) -> tuple[Risk, ...]:
        return tuple(r for r in self.risks if r.category is category)

    def by_level(self, level: RiskLevel) -> tuple[Risk, ...]:
        return tuple(r for r in self.risks if r.level is level)

    @property
    def has_critical(self) -> bool:
        """Whether any risk is CRITICAL."""
        return any(r.level is RiskLevel.CRITICAL for r in self.risks)
