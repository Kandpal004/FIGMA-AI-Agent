"""Brand emotional positioning, differentiators, and trust signals.

The emotional core of the brand: the :class:`EmotionalPositioning` (the feeling the
brand owns), the :class:`BrandDifferentiator` s (the defensible reasons to choose it),
and the :class:`TrustSignal` s (the credibility the brand must project). All cited —
downstream design must serve these; here they are decided, not rendered.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import (
    BrandDifferentiatorId,
    BrandEvidenceId,
    TrustSignalId,
)
from brand.domain.shared.value_objects import (
    Confidence,
    EmotionKind,
    Salience,
    TrustSignalKind,
)

__all__ = [
    "BrandDifferentiator",
    "EmotionalPositioning",
    "InvalidEmotionalError",
    "TrustSignal",
]


class InvalidEmotionalError(DesignDirectorError):
    """Raised when an emotional value object is constructed with invalid data."""

    code = "invalid_brand_emotional"
    http_status = 422


@dataclass(frozen=True, slots=True)
class EmotionalPositioning:
    """The cited feeling the brand owns.

    Attributes:
        primary_emotion: The dominant emotion the brand evokes.
        emotional_benefit: The emotional payoff for the customer.
        feeling_target: How the customer should feel about themselves using the brand.
        supporting_emotions: Secondary emotions in play.
        evidence_ids: The evidence supporting it.
    """

    primary_emotion: EmotionKind
    emotional_benefit: str
    feeling_target: str = ""
    supporting_emotions: tuple[EmotionKind, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.emotional_benefit or not self.emotional_benefit.strip():
            raise InvalidEmotionalError(
                "EmotionalPositioning.emotional_benefit must be non-empty."
            )
        object.__setattr__(self, "supporting_emotions", tuple(self.supporting_emotions))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BrandDifferentiator:
    """One cited, defensible reason to choose the brand.

    Attributes:
        id: Differentiator identity.
        claim: The differentiating claim.
        defensibility: Why it is hard for competitors to copy.
        versus: The alternative it differentiates against.
        salience: How prominent it should be.
        evidence_ids: The evidence supporting it.
    """

    id: BrandDifferentiatorId
    claim: str
    defensibility: str = ""
    versus: str = ""
    salience: Salience = Salience(3)
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.claim or not self.claim.strip():
            raise InvalidEmotionalError("BrandDifferentiator.claim must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class TrustSignal:
    """One cited trust signal the brand must project.

    Attributes:
        id: Signal identity.
        kind: The kind of trust signal.
        rationale: Why the brand needs it.
        salience: How prominent it should be.
        confidence: Confidence in its importance.
        evidence_ids: The evidence supporting it.
    """

    id: TrustSignalId
    kind: TrustSignalKind
    rationale: str
    salience: Salience = Salience(3)
    confidence: Confidence = Confidence(0.7)
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.rationale or not self.rationale.strip():
            raise InvalidEmotionalError("TrustSignal.rationale must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
