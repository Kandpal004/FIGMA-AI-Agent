"""The language-archetype knowledge base — the nineteen supported design languages, codified.

For each supported :class:`LanguageArchetype` this encodes its visual signature: style, luxury
and minimalism levels, density, weight, contrast, rhythm, distinctive traits, colour strategy,
type ratio, spacing base, essence, influences, and the character of its four expressive media.
This is the design judgement of an Apple/Pentagram/Stripe-calibre team expressed as data — the
rule-based designer is a thin, testable mapping over it.

Pure data over the shared value objects. No I/O, no framework.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.value_objects import (
    ColorStrategy,
    ContrastLevel,
    Density,
    LanguageArchetype,
    Rhythm,
    VisualStyle,
    VisualWeight,
)

__all__ = ["ArchetypeDescriptor", "descriptor_for"]

_A = LanguageArchetype
_S = VisualStyle
_D = Density
_W = VisualWeight
_C = ContrastLevel
_R = Rhythm
_CS = ColorStrategy


class UnknownArchetypeError(DesignDirectorError):
    """Raised when no descriptor exists for an archetype."""

    code = "design_language_unknown_archetype"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ArchetypeDescriptor:
    """The codified visual signature of one language archetype."""

    archetype: LanguageArchetype
    visual_style: VisualStyle
    luxury: int
    minimalism: int
    density: Density
    weight: VisualWeight
    contrast: ContrastLevel
    rhythm: Rhythm
    traits: tuple[str, ...]
    color_strategy: ColorStrategy
    accent_count: int
    type_ratio: float
    spacing_base: int
    essence: str
    influences: tuple[str, ...]
    type_character: str
    icon_character: str
    illustration_character: str
    photography_character: str


_DESCRIPTORS: tuple[ArchetypeDescriptor, ...] = (
    ArchetypeDescriptor(_A.APPLE, _S.MINIMAL, 5, 5, _D.SPACIOUS, _W.LIGHT, _C.HIGH, _R.RELAXED,
        ("refined", "confident", "precise", "calm"), _CS.NEUTRAL_ACCENT, 1, 1.25, 8,
        "Precision and restraint; the product is the hero.", ("clarity", "craft"),
        "Crisp neutral sans with generous leading.", "Thin, geometric, consistent.",
        "Sparingly used, purposeful.", "Clean product photography on white."),
    ArchetypeDescriptor(_A.SHOPIFY_POLARIS, _S.UTILITARIAN, 2, 3, _D.COMFORTABLE, _W.BALANCED, _C.MEDIUM, _R.MEASURED,
        ("clear", "efficient", "accessible"), _CS.NEUTRAL_ACCENT, 1, 1.2, 8,
        "Merchant-first clarity and efficiency.", ("usability", "accessibility"),
        "Legible, practical sans.", "Rounded, friendly, functional.",
        "Functional spot illustration.", "Contextual, honest imagery."),
    ArchetypeDescriptor(_A.MATERIAL_3, _S.BOLD, 2, 2, _D.COMFORTABLE, _W.BALANCED, _C.MEDIUM, _R.MEASURED,
        ("expressive", "systematic", "dynamic"), _CS.VIBRANT, 2, 1.2, 8,
        "Adaptive, expressive systematic design.", ("tokens", "motion"),
        "Flexible, expressive type.", "Filled, expressive icon set.",
        "Bold, colourful illustration.", "Vivid, energetic imagery."),
    ArchetypeDescriptor(_A.ATLASSIAN, _S.UTILITARIAN, 2, 3, _D.COMPACT, _W.BALANCED, _C.MEDIUM, _R.MEASURED,
        ("dependable", "organised", "clear"), _CS.NEUTRAL_ACCENT, 1, 1.2, 8,
        "Dependable clarity for complex work.", ("structure", "teams"),
        "Neutral, dependable sans.", "Simple, consistent line icons.",
        "Explanatory illustration.", "Team-in-context photography."),
    ArchetypeDescriptor(_A.LINEAR, _S.TECHNICAL, 3, 5, _D.COMPACT, _W.LIGHT, _C.DRAMATIC, _R.TIGHT,
        ("sharp", "fast", "focused", "dark"), _CS.HIGH_CONTRAST_BW, 1, 1.2, 8,
        "Fast, focused, keyboard-first precision.", ("speed", "focus"),
        "Tight, technical mono-adjacent sans.", "Minimal, sharp line icons.",
        "Rare, abstract.", "Dark, high-contrast product shots."),
    ArchetypeDescriptor(_A.STRIPE, _S.TECHNICAL, 4, 4, _D.SPACIOUS, _W.LIGHT, _C.HIGH, _R.RELAXED,
        ("trustworthy", "precise", "gradient-crafted"), _CS.DUOTONE, 2, 1.25, 8,
        "Developer-grade precision with crafted depth.", ("trust", "craft"),
        "Clean, precise sans.", "Fine, geometric icons.",
        "Signature gradient illustration.", "Abstract, crafted visuals."),
    ArchetypeDescriptor(_A.NOTION, _S.EDITORIAL, 3, 4, _D.SPACIOUS, _W.LIGHT, _C.MEDIUM, _R.RELAXED,
        ("calm", "flexible", "literary"), _CS.MONOCHROME, 1, 1.2, 8,
        "Calm, flexible, document-like canvas.", ("writing", "flexibility"),
        "Readable serif/sans blend.", "Simple, monoline icons.",
        "Playful hand-drawn accents.", "Minimal, incidental imagery."),
    ArchetypeDescriptor(_A.NIKE, _S.BOLD, 3, 3, _D.COMFORTABLE, _W.HEAVY, _C.DRAMATIC, _R.TIGHT,
        ("energetic", "confident", "athletic"), _CS.HIGH_CONTRAST_BW, 1, 1.333, 8,
        "Bold, athletic energy and motion.", ("movement", "confidence"),
        "Heavy, condensed display type.", "Bold, dynamic icons.",
        "Dynamic action illustration.", "High-energy athletic photography."),
    ArchetypeDescriptor(_A.GYMSHARK, _S.BOLD, 3, 3, _D.COMFORTABLE, _W.HEAVY, _C.DRAMATIC, _R.MEASURED,
        ("bold", "community", "aspirational"), _CS.HIGH_CONTRAST_BW, 1, 1.333, 8,
        "Community-driven, aspirational strength.", ("community", "aspiration"),
        "Strong, condensed sans.", "Bold, solid icons.",
        "Motivational graphic accents.", "Aspirational fitness photography."),
    ArchetypeDescriptor(_A.AESOP, _S.EDITORIAL, 5, 4, _D.AIRY, _W.LIGHT, _C.MEDIUM, _R.RELAXED,
        ("apothecary", "literary", "tactile", "restrained"), _CS.EARTHY, 1, 1.2, 8,
        "Apothecary restraint; considered and literary.", ("editorial", "craft"),
        "Refined book-like serif.", "Minimal, understated marks.",
        "Rare, editorial.", "Warm, tactile still-life photography."),
    ArchetypeDescriptor(_A.DYSON, _S.TECHNICAL, 4, 4, _D.SPACIOUS, _W.BALANCED, _C.HIGH, _R.MEASURED,
        ("engineered", "precise", "innovative"), _CS.NEUTRAL_ACCENT, 1, 1.25, 8,
        "Engineering made visible and premium.", ("engineering", "innovation"),
        "Technical, precise sans.", "Fine, engineered line icons.",
        "Exploded-diagram illustration.", "Studio product engineering shots."),
    ArchetypeDescriptor(_A.NOTHING, _S.TECHNICAL, 4, 5, _D.AIRY, _W.LIGHT, _C.DRAMATIC, _R.RELAXED,
        ("transparent", "dot-matrix", "distinctive"), _CS.HIGH_CONTRAST_BW, 1, 1.25, 8,
        "Transparent, dot-matrix minimal distinctiveness.", ("transparency", "signature"),
        "Dot-matrix inspired mono type.", "Pixel/dot-grid icons.",
        "Technical wireframe illustration.", "Transparent, exposed product shots."),
    ArchetypeDescriptor(_A.LUXURY_FASHION, _S.LUXE, 5, 5, _D.AIRY, _W.LIGHT, _C.DRAMATIC, _R.RELAXED,
        ("elegant", "timeless", "editorial", "exclusive"), _CS.MONOCHROME, 0, 1.333, 8,
        "Editorial elegance; whitespace as luxury.", ("couture", "editorial"),
        "High-contrast display serif.", "None or hairline marks.",
        "None.", "Editorial fashion photography."),
    ArchetypeDescriptor(_A.LUXURY_BEAUTY, _S.LUXE, 5, 5, _D.AIRY, _W.LIGHT, _C.MEDIUM, _R.RELAXED,
        ("elegant", "sensorial", "refined", "calm"), _CS.EARTHY, 1, 1.25, 8,
        "Sensorial refinement; calm, considered luxury.", ("beauty", "ritual"),
        "Refined serif with airy leading.", "Delicate, minimal marks.",
        "Rare botanical accent.", "Soft, sensorial product photography."),
    ArchetypeDescriptor(_A.PREMIUM_ELECTRONICS, _S.MINIMAL, 4, 5, _D.SPACIOUS, _W.LIGHT, _C.HIGH, _R.MEASURED,
        ("precise", "modern", "confident"), _CS.NEUTRAL_ACCENT, 1, 1.25, 8,
        "Modern precision; product as sculpture.", ("hardware", "precision"),
        "Clean modern sans.", "Thin geometric icons.",
        "Minimal technical illustration.", "Sculptural product photography."),
    ArchetypeDescriptor(_A.PREMIUM_SUPPLEMENTS, _S.WARM, 3, 4, _D.SPACIOUS, _W.BALANCED, _C.MEDIUM, _R.MEASURED,
        ("clean", "trustworthy", "wellness"), _CS.MUTED, 1, 1.2, 8,
        "Clean wellness; trustworthy and calm.", ("health", "trust"),
        "Warm, legible sans.", "Rounded, calm icons.",
        "Soft ingredient illustration.", "Clean, natural product photography."),
    ArchetypeDescriptor(_A.ENTERPRISE_SAAS, _S.UTILITARIAN, 2, 3, _D.COMPACT, _W.BALANCED, _C.MEDIUM, _R.MEASURED,
        ("dependable", "systematic", "scalable"), _CS.NEUTRAL_ACCENT, 1, 1.2, 8,
        "Dependable, scalable, information-dense clarity.", ("scale", "systems"),
        "Neutral, dependable sans.", "Consistent line icons.",
        "Explanatory diagram illustration.", "Contextual product-in-use imagery."),
    ArchetypeDescriptor(_A.MINIMAL_EDITORIAL, _S.EDITORIAL, 4, 5, _D.AIRY, _W.LIGHT, _C.HIGH, _R.RELAXED,
        ("literary", "spare", "typographic"), _CS.MONOCHROME, 0, 1.414, 8,
        "Typography-led editorial spareness.", ("editorial", "typography"),
        "Expressive editorial serif.", "None or hairline marks.",
        "None.", "Editorial black-and-white photography."),
    ArchetypeDescriptor(_A.CUSTOM_BLEND, _S.MINIMAL, 4, 4, _D.SPACIOUS, _W.LIGHT, _C.HIGH, _R.RELAXED,
        ("bespoke", "considered", "distinctive"), _CS.NEUTRAL_ACCENT, 1, 1.25, 8,
        "A bespoke synthesis of premium influences.", ("bespoke", "synthesis"),
        "Considered custom type pairing.", "Custom minimal icon set.",
        "Bespoke illustration accents.", "Signature art direction."),
)

_BY_ARCHETYPE: dict[LanguageArchetype, ArchetypeDescriptor] = {
    d.archetype: d for d in _DESCRIPTORS
}


def descriptor_for(archetype: LanguageArchetype) -> ArchetypeDescriptor:
    """Return the codified descriptor for a language archetype."""
    descriptor = _BY_ARCHETYPE.get(archetype)
    if descriptor is None:  # pragma: no cover - all archetypes are defined
        raise UnknownArchetypeError(
            f"No descriptor for archetype {archetype.value}.",
            details={"archetype": archetype.value},
        )
    return descriptor
