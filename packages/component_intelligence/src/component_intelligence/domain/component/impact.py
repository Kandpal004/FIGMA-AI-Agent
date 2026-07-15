"""ComponentImpacts — how a component affects quality and outcomes.

:class:`ComponentImpacts` grades a component on the three non-functional dimensions (SEO,
accessibility, performance) and the three outcome effects the engine reasons about most —
conversion, friction, and trust. This is the intelligence behind "which components improve
conversion, reduce friction, and increase trust": each effect is graded and cited, so an
inclusion decision can be defended in outcome terms.

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from component_intelligence.domain.shared.ids import CIEvidenceId
from component_intelligence.domain.shared.value_objects import EffectLevel, ImpactLevel

__all__ = ["ComponentImpacts"]


@dataclass(frozen=True, slots=True)
class ComponentImpacts:
    """A component's impact on quality dimensions and outcome effects.

    Attributes:
        seo: Impact on SEO.
        accessibility: Impact on accessibility.
        performance: Impact on performance.
        conversion_effect: How strongly it improves conversion.
        friction_effect: How strongly it reduces friction.
        trust_effect: How strongly it increases trust.
        evidence_ids: The evidence grounding the impacts.
    """

    seo: ImpactLevel = ImpactLevel.NEUTRAL
    accessibility: ImpactLevel = ImpactLevel.NEUTRAL
    performance: ImpactLevel = ImpactLevel.NEUTRAL
    conversion_effect: EffectLevel = EffectLevel.NONE
    friction_effect: EffectLevel = EffectLevel.NONE
    trust_effect: EffectLevel = EffectLevel.NONE
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def improves_conversion(self) -> bool:
        return self.conversion_effect in (EffectLevel.STRONG, EffectLevel.MODERATE)

    @property
    def reduces_friction(self) -> bool:
        return self.friction_effect in (EffectLevel.STRONG, EffectLevel.MODERATE)

    @property
    def builds_trust(self) -> bool:
        return self.trust_effect in (EffectLevel.STRONG, EffectLevel.MODERATE)
