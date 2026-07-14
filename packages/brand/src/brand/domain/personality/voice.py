"""Brand voice and tone — how the brand sounds, and how it flexes.

A :class:`BrandVoice` is the constant character of the brand's language, placed on the
four tone-of-voice dimensions (formality, humor, respect, enthusiasm) with do/don't
guardrails. A :class:`BrandTone` is the dominant register, and :class:`ToneModulation`
records how the tone flexes by context (reassuring at checkout, celebratory
post-purchase) — voice is fixed, tone adapts. Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import (
    MessagingTone,
    Percentage,
    VoiceDimension,
)

__all__ = ["BrandTone", "BrandVoice", "InvalidVoiceError", "ToneModulation"]


class InvalidVoiceError(DesignDirectorError):
    """Raised when brand voice/tone is constructed with invalid data."""

    code = "invalid_brand_voice"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandVoice:
    """The cited, constant character of the brand's language.

    Attributes:
        dimensions: The brand's position on each tone-of-voice spectrum (0 = first pole,
            1 = second pole), read-only.
        principles: How the voice behaves (do).
        avoid: What the voice never does (don't).
        signature_words: Words/phrases the brand favours.
        evidence_ids: The evidence supporting it.
    """

    dimensions: Mapping[VoiceDimension, Percentage] = field(
        default_factory=lambda: MappingProxyType({})
    )
    principles: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    signature_words: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.dimensions, MappingProxyType):
            object.__setattr__(self, "dimensions", MappingProxyType(dict(self.dimensions)))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "avoid", tuple(self.avoid))
        object.__setattr__(self, "signature_words", tuple(self.signature_words))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ToneModulation:
    """How the tone flexes in a particular context.

    Attributes:
        context: The context/moment (e.g. "checkout", "error", "post-purchase").
        adjustment: How the tone shifts there.
    """

    context: str
    adjustment: str

    def __post_init__(self) -> None:
        if not self.context or not self.context.strip():
            raise InvalidVoiceError("ToneModulation.context must be non-empty.")
        if not self.adjustment or not self.adjustment.strip():
            raise InvalidVoiceError("ToneModulation.adjustment must be non-empty.")


@dataclass(frozen=True, slots=True)
class BrandTone:
    """The cited dominant tone and its contextual modulations.

    Attributes:
        dominant: The dominant tone register.
        modulations: How the tone flexes by context.
        evidence_ids: The evidence supporting it.
    """

    dominant: MessagingTone
    modulations: tuple[ToneModulation, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "modulations", tuple(self.modulations))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
