"""Business risks — what could go wrong, and how likely.

A :class:`BusinessRisk` scores a threat on severity × likelihood into a deterministic
level (critical / high / moderate / low) and carries the mitigation strategy. The
:class:`RiskRegister` is the immutable collection, and it computes the report's overall
risk posture. Every risk is cited — including evidence-gap risks the engine raises when
grounding is thin.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import BusinessRiskId, StrategyEvidenceId
from strategy.domain.shared.value_objects import (
    Likelihood,
    RiskCategory,
    RiskLevel,
    Severity,
)

__all__ = ["BusinessRisk", "InvalidRiskError", "RiskRegister"]


class InvalidRiskError(DesignDirectorError):
    """Raised when a business risk is constructed with invalid data."""

    code = "invalid_business_risk"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BusinessRisk:
    """One cited, scored business risk.

    Attributes:
        id: Risk identity.
        category: The risk category.
        description: What the risk is.
        severity: How bad it would be (1–5).
        likelihood: How likely it is (1–5).
        mitigation: The strategy to reduce it.
        evidence_ids: The evidence supporting it.
    """

    id: BusinessRiskId
    category: RiskCategory
    description: str
    severity: Severity
    likelihood: Likelihood
    mitigation: str = ""
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise InvalidRiskError("BusinessRisk.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def score(self) -> int:
        """Severity × likelihood, in ``[1, 25]``."""
        return int(self.severity) * int(self.likelihood)

    @property
    def level(self) -> RiskLevel:
        score = self.score
        if score >= 15:
            return RiskLevel.CRITICAL
        if score >= 9:
            return RiskLevel.HIGH
        if score >= 4:
            return RiskLevel.MODERATE
        return RiskLevel.LOW


@dataclass(frozen=True, slots=True)
class RiskRegister:
    """An immutable register of business risks."""

    risks: tuple[BusinessRisk, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "risks", tuple(self.risks))

    @classmethod
    def of(cls, risks: Iterable[BusinessRisk]) -> RiskRegister:
        return cls(risks=tuple(risks))

    def __len__(self) -> int:
        return len(self.risks)

    def __iter__(self):
        return iter(self.risks)

    def by_severity(self) -> tuple[BusinessRisk, ...]:
        return tuple(sorted(self.risks, key=lambda r: r.score, reverse=True))

    @property
    def overall_level(self) -> RiskLevel:
        """The highest risk level present (LOW if the register is empty)."""
        if not self.risks:
            return RiskLevel.LOW
        return max(self.risks, key=lambda r: r.score).level

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return tuple(eid for r in self.risks for eid in r.evidence_ids)
