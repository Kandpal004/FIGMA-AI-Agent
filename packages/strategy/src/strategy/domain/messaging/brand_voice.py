"""Brand voice & personality — the register the brand speaks in.

:class:`BrandVoice` sets the tone and the do/don't guardrails; :class:`BrandPersonality`
names the traits and archetype the brand embodies. Both are cited and inform — but do
not write — every word the experience later says.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import MessagingTone, PersonalityTrait

__all__ = ["BrandPersonality", "BrandVoice", "InvalidBrandVoiceError"]


class InvalidBrandVoiceError(DesignDirectorError):
    """Raised when brand voice/personality is constructed with invalid data."""

    code = "invalid_brand_voice"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandVoice:
    """The cited tone and guardrails of the brand's voice.

    Attributes:
        tone: The dominant tone.
        principles: How the voice should behave (do).
        avoid: What the voice should never do (don't).
        vocabulary: Signature words/phrases the brand favours.
        evidence_ids: The evidence supporting it.
    """

    tone: MessagingTone
    principles: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    vocabulary: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "avoid", tuple(self.avoid))
        object.__setattr__(self, "vocabulary", tuple(self.vocabulary))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BrandPersonality:
    """The cited personality the brand embodies.

    Attributes:
        traits: The personality traits (Aaker dimensions).
        archetype: The brand archetype (e.g. "the Sage", "the Creator").
        descriptors: Free-form personality descriptors.
        evidence_ids: The evidence supporting it.
    """

    traits: tuple[PersonalityTrait, ...] = ()
    archetype: str = ""
    descriptors: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "traits", tuple(self.traits))
        object.__setattr__(self, "descriptors", tuple(self.descriptors))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
