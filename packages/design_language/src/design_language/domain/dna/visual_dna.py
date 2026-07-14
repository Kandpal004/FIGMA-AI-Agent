"""The Visual DNA — the distilled visual identity the whole language grows from.

A :class:`VisualDNA` is the seed of the design language: its visual style, its luxury and
minimalism levels, its density, weight, contrast, and rhythm, its one-line essence, and the
distinctive traits that make it *this* brand and not a generic template. Every philosophy,
token, personality, and rule elaborates or constrains the DNA. It carries no concrete colour,
font, or pixel — it fixes the *character* those must express.

An undifferentiated DNA — default everything, no distinctive traits — is the tell of an
AI-generated look; a usable DNA must carry traits, so the aggregate can refuse a generic
language.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId
from design_language.domain.shared.value_objects import (
    ContrastLevel,
    Density,
    Level,
    Rhythm,
    Tag,
    VisualStyle,
    VisualWeight,
)

__all__ = ["InvalidVisualDNAError", "VisualDNA"]


class InvalidVisualDNAError(DesignDirectorError):
    """Raised when a visual DNA is constructed with invalid data."""

    code = "invalid_design_language_dna"
    http_status = 422


@dataclass(frozen=True, slots=True)
class VisualDNA:
    """The distilled visual identity of the design language.

    Attributes:
        visual_style: The overall visual posture.
        luxury_level: How luxurious the language should feel (1–5).
        minimalism_level: How minimal the language should be (1–5).
        density: How tightly it packs information.
        visual_weight: Its perceived heaviness.
        contrast: Its contrast posture.
        rhythm: Its spacing/pacing rhythm.
        essence: A one-line articulation of the visual point of view.
        traits: The distinctive adjectives that make it specific (not generic).
        evidence_ids: The evidence grounding the DNA.
    """

    visual_style: VisualStyle
    luxury_level: Level
    minimalism_level: Level
    density: Density
    visual_weight: VisualWeight
    contrast: ContrastLevel
    rhythm: Rhythm
    essence: str
    traits: tuple[Tag, ...] = ()
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.essence or not self.essence.strip():
            raise InvalidVisualDNAError("VisualDNA.essence must be non-empty.")
        object.__setattr__(self, "traits", tuple(dict.fromkeys(self.traits)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def is_distinctive(self) -> bool:
        """Whether the DNA carries the distinctive traits a premium language needs."""
        return len(self.traits) >= 2

    def signature(self) -> tuple[str, int, int, str, str]:
        """The compact fingerprint the consistency rules and visual graph are built from."""
        return (
            self.visual_style.value,
            int(self.luxury_level),
            int(self.minimalism_level),
            self.density.value,
            self.contrast.value,
        )

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids
