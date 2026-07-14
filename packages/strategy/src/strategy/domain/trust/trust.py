"""Trust strategy — the credibility the experience must establish.

A :class:`TrustStrategy` names the :class:`TrustElement` s the experience must carry,
in priority order, each tied to the journey phase where it matters, and a
:class:`SocialProofStrategy` for how proof should be marshalled. Trust is decided
here; where and how it renders is a later phase.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId, TrustElementId
from strategy.domain.shared.value_objects import (
    JourneyPhase,
    Priority,
    SocialProofKind,
    TrustElementKind,
)

__all__ = [
    "InvalidTrustError",
    "SocialProofStrategy",
    "TrustElement",
    "TrustStrategy",
]


class InvalidTrustError(DesignDirectorError):
    """Raised when trust strategy is constructed with invalid data."""

    code = "invalid_trust_strategy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class TrustElement:
    """One cited trust element the experience must supply.

    Attributes:
        id: Element identity.
        kind: The kind of trust element.
        rationale: Why it is required.
        phase: The journey phase where it matters most.
        priority: Its priority relative to other trust elements.
        evidence_ids: The evidence supporting it.
    """

    id: TrustElementId
    kind: TrustElementKind
    rationale: str
    phase: JourneyPhase
    priority: Priority
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.rationale or not self.rationale.strip():
            raise InvalidTrustError("TrustElement.rationale must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class SocialProofStrategy:
    """The cited social-proof approach.

    Attributes:
        kinds: The kinds of social proof to deploy.
        placement_intent: Strategic intent for where proof carries weight.
        evidence_ids: The evidence supporting it.
    """

    kinds: tuple[SocialProofKind, ...] = ()
    placement_intent: str = ""
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "kinds", tuple(self.kinds))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class TrustStrategy:
    """The complete, cited trust strategy."""

    elements: tuple[TrustElement, ...] = ()
    social_proof: SocialProofStrategy = SocialProofStrategy()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "elements", tuple(self.elements))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def by_priority(self) -> tuple[TrustElement, ...]:
        return tuple(sorted(self.elements, key=lambda e: int(e.priority), reverse=True))

    def all_evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return (
            *self.evidence_ids,
            *self.social_proof.evidence_ids,
            *(eid for e in self.elements for eid in e.evidence_ids),
        )
