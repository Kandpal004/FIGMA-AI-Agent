"""The Brand Character — the consolidated personality of the brand.

:class:`BrandCharacter` groups the outputs of personality synthesis — the archetype
blend, the personality and attributes, the voice, and the tone — into one cohesive,
cited value object the report composes.

Pure domain: standard library and the personality sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.personality.archetype import ArchetypeBlend
from brand.domain.personality.personality import BrandPersonality
from brand.domain.personality.voice import BrandTone, BrandVoice
from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["BrandCharacter"]


@dataclass(frozen=True, slots=True)
class BrandCharacter:
    """The consolidated, cited brand character.

    Attributes:
        archetype: The archetype the brand embodies.
        personality: The traits and attributes.
        voice: The constant character of the brand's language.
        tone: The dominant tone and its modulations.
    """

    archetype: ArchetypeBlend
    personality: BrandPersonality
    voice: BrandVoice
    tone: BrandTone

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return (
            *self.archetype.evidence_ids,
            *self.personality.all_evidence_ids(),
            *self.voice.evidence_ids,
            *self.tone.evidence_ids,
        )
