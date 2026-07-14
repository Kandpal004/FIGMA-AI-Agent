"""Category creative profiles — the deterministic brand-strategy knowledge base.

Each :class:`BrandCategory` maps to a :class:`CategoryProfile`: the archetype, tone,
and creative languages a world-class brand in that category tends to express. This is
the explainable knowledge the rule-based strategist reasons from — a codification of how
Interbrand/Pentagram/Landor-grade brands are built by register, not a random generator.

Pure data: standard library and the shared value objects only.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.shared.value_objects import (
    BrandArchetype,
    BrandCategory,
    ColorTemperament,
    ComponentWeight,
    ContrastLevel,
    CornerLanguage,
    EmotionKind,
    IconStyle,
    IllustrationStyle,
    MessagingTone,
    MotionCharacter,
    PhotoTreatment,
    SpacingDensity,
    TypeVoice,
    UITexture,
)

__all__ = ["CategoryProfile", "profile_for"]


@dataclass(frozen=True, slots=True)
class CategoryProfile:
    """The creative register a brand category expresses."""

    archetype: BrandArchetype
    tone: MessagingTone
    emotion: EmotionKind
    temperament: ColorTemperament
    contrast: ContrastLevel
    display_voice: TypeVoice
    body_voice: TypeVoice
    density: SpacingDensity
    photo: PhotoTreatment
    illustration: IllustrationStyle
    icon: IconStyle
    motion: MotionCharacter
    corner: CornerLanguage
    weight: ComponentWeight
    texture: UITexture
    adjectives: tuple[str, ...]


_PROFILES: dict[BrandCategory, CategoryProfile] = {
    BrandCategory.LUXURY: CategoryProfile(
        BrandArchetype.RULER, MessagingTone.LUXURIOUS, EmotionKind.EXCLUSIVITY,
        ColorTemperament.NEUTRAL, ContrastLevel.DRAMATIC, TypeVoice.EDITORIAL_SERIF,
        TypeVoice.HUMANIST_SANS, SpacingDensity.AIRY, PhotoTreatment.EDITORIAL,
        IllustrationStyle.NONE, IconStyle.LINE, MotionCharacter.SUBTLE,
        CornerLanguage.SHARP, ComponentWeight.LIGHT, UITexture.FLAT,
        ("elegant", "refined", "exclusive"),
    ),
    BrandCategory.PREMIUM: CategoryProfile(
        BrandArchetype.SAGE, MessagingTone.AUTHORITATIVE, EmotionKind.CONFIDENCE,
        ColorTemperament.NEUTRAL, ContrastLevel.HIGH, TypeVoice.TRANSITIONAL_SERIF,
        TypeVoice.HUMANIST_SANS, SpacingDensity.AIRY, PhotoTreatment.STUDIO,
        IllustrationStyle.NONE, IconStyle.LINE, MotionCharacter.FLUID,
        CornerLanguage.SLIGHTLY_ROUNDED, ComponentWeight.REGULAR, UITexture.SUBTLE_DEPTH,
        ("premium", "crafted", "considered"),
    ),
    BrandCategory.MINIMAL: CategoryProfile(
        BrandArchetype.INNOCENT, MessagingTone.MINIMAL, EmotionKind.CALM,
        ColorTemperament.NEUTRAL, ContrastLevel.LOW, TypeVoice.GEOMETRIC_SANS,
        TypeVoice.GEOMETRIC_SANS, SpacingDensity.AIRY, PhotoTreatment.MINIMAL,
        IllustrationStyle.NONE, IconStyle.LINE, MotionCharacter.MINIMAL,
        CornerLanguage.SHARP, ComponentWeight.LIGHT, UITexture.FLAT,
        ("minimal", "calm", "essential"),
    ),
    BrandCategory.TECHNICAL: CategoryProfile(
        BrandArchetype.CREATOR, MessagingTone.TECHNICAL, EmotionKind.CONFIDENCE,
        ColorTemperament.COOL, ContrastLevel.HIGH, TypeVoice.GROTESQUE_SANS,
        TypeVoice.MONOSPACE, SpacingDensity.BALANCED, PhotoTreatment.DOCUMENTARY,
        IllustrationStyle.GEOMETRIC, IconStyle.LINE, MotionCharacter.PRECISE,
        CornerLanguage.SLIGHTLY_ROUNDED, ComponentWeight.REGULAR, UITexture.FLAT,
        ("precise", "technical", "clear"),
    ),
    BrandCategory.LIFESTYLE: CategoryProfile(
        BrandArchetype.EXPLORER, MessagingTone.WARM, EmotionKind.BELONGING,
        ColorTemperament.WARM, ContrastLevel.MEDIUM, TypeVoice.HUMANIST_SANS,
        TypeVoice.HUMANIST_SANS, SpacingDensity.BALANCED, PhotoTreatment.LIFESTYLE,
        IllustrationStyle.ORGANIC, IconStyle.ROUNDED, MotionCharacter.FLUID,
        CornerLanguage.ROUNDED, ComponentWeight.REGULAR, UITexture.SUBTLE_DEPTH,
        ("warm", "authentic", "inviting"),
    ),
    BrandCategory.MASS_MARKET: CategoryProfile(
        BrandArchetype.EVERYPERSON, MessagingTone.WARM, EmotionKind.REASSURANCE,
        ColorTemperament.WARM, ContrastLevel.MEDIUM, TypeVoice.GROTESQUE_SANS,
        TypeVoice.HUMANIST_SANS, SpacingDensity.COMPACT, PhotoTreatment.LIFESTYLE,
        IllustrationStyle.FLAT, IconStyle.ROUNDED, MotionCharacter.PLAYFUL,
        CornerLanguage.ROUNDED, ComponentWeight.MEDIUM, UITexture.SUBTLE_DEPTH,
        ("friendly", "accessible", "clear"),
    ),
    BrandCategory.FASHION: CategoryProfile(
        BrandArchetype.LOVER, MessagingTone.ELEGANT, EmotionKind.DESIRE,
        ColorTemperament.NEUTRAL, ContrastLevel.DRAMATIC, TypeVoice.DISPLAY,
        TypeVoice.HUMANIST_SANS, SpacingDensity.AIRY, PhotoTreatment.EDITORIAL,
        IllustrationStyle.NONE, IconStyle.LINE, MotionCharacter.DRAMATIC,
        CornerLanguage.SHARP, ComponentWeight.LIGHT, UITexture.FLAT,
        ("expressive", "bold", "editorial"),
    ),
    BrandCategory.BEAUTY: CategoryProfile(
        BrandArchetype.LOVER, MessagingTone.ELEGANT, EmotionKind.ASPIRATION,
        ColorTemperament.WARM, ContrastLevel.MEDIUM, TypeVoice.EDITORIAL_SERIF,
        TypeVoice.HUMANIST_SANS, SpacingDensity.AIRY, PhotoTreatment.EDITORIAL,
        IllustrationStyle.ORGANIC, IconStyle.LINE, MotionCharacter.FLUID,
        CornerLanguage.ROUNDED, ComponentWeight.LIGHT, UITexture.SUBTLE_DEPTH,
        ("sensorial", "elegant", "radiant"),
    ),
    BrandCategory.HEALTHCARE: CategoryProfile(
        BrandArchetype.CAREGIVER, MessagingTone.REASSURING, EmotionKind.REASSURANCE,
        ColorTemperament.COOL, ContrastLevel.MEDIUM, TypeVoice.HUMANIST_SANS,
        TypeVoice.HUMANIST_SANS, SpacingDensity.BALANCED, PhotoTreatment.DOCUMENTARY,
        IllustrationStyle.LINE, IconStyle.ROUNDED, MotionCharacter.SUBTLE,
        CornerLanguage.ROUNDED, ComponentWeight.REGULAR, UITexture.SUBTLE_DEPTH,
        ("caring", "trustworthy", "clear"),
    ),
    BrandCategory.SUPPLEMENTS: CategoryProfile(
        BrandArchetype.HERO, MessagingTone.BOLD, EmotionKind.EMPOWERMENT,
        ColorTemperament.COOL, ContrastLevel.HIGH, TypeVoice.GROTESQUE_SANS,
        TypeVoice.HUMANIST_SANS, SpacingDensity.COMPACT, PhotoTreatment.STUDIO,
        IllustrationStyle.GEOMETRIC, IconStyle.SOLID, MotionCharacter.PRECISE,
        CornerLanguage.ROUNDED, ComponentWeight.BOLD, UITexture.SUBTLE_DEPTH,
        ("energetic", "credible", "direct"),
    ),
    BrandCategory.ELECTRONICS: CategoryProfile(
        BrandArchetype.CREATOR, MessagingTone.TECHNICAL, EmotionKind.CONFIDENCE,
        ColorTemperament.COOL, ContrastLevel.HIGH, TypeVoice.GEOMETRIC_SANS,
        TypeVoice.GROTESQUE_SANS, SpacingDensity.BALANCED, PhotoTreatment.STUDIO,
        IllustrationStyle.GEOMETRIC, IconStyle.LINE, MotionCharacter.PRECISE,
        CornerLanguage.SLIGHTLY_ROUNDED, ComponentWeight.REGULAR, UITexture.LAYERED,
        ("modern", "precise", "innovative"),
    ),
    BrandCategory.FURNITURE: CategoryProfile(
        BrandArchetype.CREATOR, MessagingTone.WARM, EmotionKind.CALM,
        ColorTemperament.WARM, ContrastLevel.MEDIUM, TypeVoice.TRANSITIONAL_SERIF,
        TypeVoice.HUMANIST_SANS, SpacingDensity.AIRY, PhotoTreatment.LIFESTYLE,
        IllustrationStyle.LINE, IconStyle.LINE, MotionCharacter.FLUID,
        CornerLanguage.SLIGHTLY_ROUNDED, ComponentWeight.REGULAR, UITexture.SUBTLE_DEPTH,
        ("crafted", "warm", "considered"),
    ),
    BrandCategory.ENTERPRISE: CategoryProfile(
        BrandArchetype.RULER, MessagingTone.AUTHORITATIVE, EmotionKind.CONFIDENCE,
        ColorTemperament.COOL, ContrastLevel.MEDIUM, TypeVoice.GROTESQUE_SANS,
        TypeVoice.HUMANIST_SANS, SpacingDensity.BALANCED, PhotoTreatment.DOCUMENTARY,
        IllustrationStyle.GEOMETRIC, IconStyle.LINE, MotionCharacter.PRECISE,
        CornerLanguage.SLIGHTLY_ROUNDED, ComponentWeight.REGULAR, UITexture.FLAT,
        ("professional", "robust", "trusted"),
    ),
}


def profile_for(category: BrandCategory) -> CategoryProfile:
    """Return the creative profile for a brand category."""
    return _PROFILES[category]
