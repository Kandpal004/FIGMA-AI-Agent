"""The Emotional Strategy — the consolidated emotional core of the brand.

:class:`EmotionalStrategy` groups the emotional positioning, the differentiators, and
the trust signals into one cohesive, cited value object the report composes.

Pure domain: standard library and the emotional sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.emotional.emotional import (
    BrandDifferentiator,
    EmotionalPositioning,
    TrustSignal,
)
from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["EmotionalStrategy"]


@dataclass(frozen=True, slots=True)
class EmotionalStrategy:
    """The consolidated, cited emotional core of the brand.

    Attributes:
        positioning: The feeling the brand owns.
        differentiators: The defensible reasons to choose it.
        trust_signals: The credibility the brand must project.
    """

    positioning: EmotionalPositioning
    differentiators: tuple[BrandDifferentiator, ...] = ()
    trust_signals: tuple[TrustSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "differentiators", tuple(self.differentiators))
        object.__setattr__(self, "trust_signals", tuple(self.trust_signals))

    def differentiators_by_salience(self) -> tuple[BrandDifferentiator, ...]:
        return tuple(sorted(self.differentiators, key=lambda d: int(d.salience), reverse=True))

    def trust_by_salience(self) -> tuple[TrustSignal, ...]:
        return tuple(sorted(self.trust_signals, key=lambda t: int(t.salience), reverse=True))

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return (
            *self.positioning.evidence_ids,
            *(eid for d in self.differentiators for eid in d.evidence_ids),
            *(eid for t in self.trust_signals for eid in t.evidence_ids),
        )
