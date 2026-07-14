"""Customer psychology — the pains, objections, motivations, and emotions.

These cited value objects capture *why* a customer does or does not buy: the
:class:`PainPoint` s they feel, the :class:`Objection` s they raise (with the strategy
to answer them), the :class:`PurchaseMotivation` s that drive them, and the
:class:`EmotionalTrigger` s a strategy intends to activate. Downstream design must
serve these; here they are decided, not rendered.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import (
    Confidence,
    EmotionKind,
    JourneyPhase,
    Severity,
)

__all__ = [
    "EmotionalTrigger",
    "InvalidPsychologyError",
    "Objection",
    "PainPoint",
    "PurchaseMotivation",
]


class InvalidPsychologyError(DesignDirectorError):
    """Raised when a psychology value object is constructed with invalid data."""

    code = "invalid_customer_psychology"
    http_status = 422


def _require(value: str, field: str) -> None:
    if not value or not value.strip():
        raise InvalidPsychologyError(f"{field} must be non-empty.")


@dataclass(frozen=True, slots=True)
class PainPoint:
    """A cited customer pain the experience must relieve.

    Attributes:
        description: The pain, in the customer's terms.
        severity: How acute it is.
        phase: Where in the journey it bites.
        evidence_ids: The evidence supporting it.
    """

    description: str
    severity: Severity
    phase: JourneyPhase
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.description, "PainPoint.description")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class Objection:
    """A cited purchase objection and the strategy to answer it.

    Attributes:
        objection: The objection a customer raises.
        rebuttal_strategy: How the experience should answer it (strategy, not copy).
        evidence_ids: The evidence supporting it.
    """

    objection: str
    rebuttal_strategy: str
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.objection, "Objection.objection")
        _require(self.rebuttal_strategy, "Objection.rebuttal_strategy")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class PurchaseMotivation:
    """A cited driver of purchase.

    Attributes:
        description: What motivates the purchase.
        weight: How strong a driver it is.
        evidence_ids: The evidence supporting it.
    """

    description: str
    weight: Confidence
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.description, "PurchaseMotivation.description")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class EmotionalTrigger:
    """A cited emotion a strategy intends to trigger.

    Attributes:
        emotion: The emotion to activate.
        trigger: The strategic trigger that activates it (not a UI element).
        intended_response: The customer response it aims to produce.
        evidence_ids: The evidence supporting it.
    """

    emotion: EmotionKind
    trigger: str
    intended_response: str = ""
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.trigger, "EmotionalTrigger.trigger")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
