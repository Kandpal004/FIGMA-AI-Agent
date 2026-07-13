"""AlternativeGenerator — the roads not taken, described deterministically.

For every stance other than the chosen one, the engine records how the strategy
would shift under that lens. These are lightweight, deterministic *summaries* (not
full nested strategies), so a caller can see the space of strategic options and why
the chosen stance prevailed.
"""

from __future__ import annotations

from reasoning.domain.alternative.alternative import AlternativeStrategy
from reasoning.domain.confidence.confidence import ConfidenceScore
from reasoning.domain.shared.ids import AlternativeId
from reasoning.domain.shared.value_objects import StrategyStance

__all__ = ["AlternativeGenerator"]

# A deterministic description of how each stance would shape the strategy.
_STANCE_PROFILE: dict[StrategyStance, tuple[str, tuple[str, ...]]] = {
    StrategyStance.BALANCED: (
        "Balance conversion, brand, accessibility, and trust evenly.",
        ("even weighting across dimensions",),
    ),
    StrategyStance.CONVERSION_FIRST: (
        "Maximise conversion, accepting more aggressive commercial cues.",
        ("prominent, high-contrast CTAs", "urgency and social proof foregrounded"),
    ),
    StrategyStance.BRAND_FIRST: (
        "Protect brand elegance and restraint over commercial pressure.",
        ("understated CTAs", "generous whitespace", "editorial typography"),
    ),
    StrategyStance.ACCESSIBILITY_FIRST: (
        "Lead with inclusive design; every choice clears WCAG first.",
        ("contrast and focus states prioritised", "simpler, more legible layouts"),
    ),
    StrategyStance.TRUST_FIRST: (
        "Foreground trust signals to reduce purchase anxiety.",
        ("reviews, guarantees, and security cues elevated",),
    ),
    StrategyStance.PERFORMANCE_FIRST: (
        "Minimise weight and sections to maximise speed.",
        ("fewer sections", "lighter media", "deferred non-critical content"),
    ),
}


class AlternativeGenerator:
    """Describes the alternative strategies for every non-chosen stance."""

    def generate(
        self, chosen_stance: StrategyStance, overall_confidence: ConfidenceScore
    ) -> tuple[AlternativeStrategy, ...]:
        alternatives: list[AlternativeStrategy] = []
        for stance in StrategyStance:
            if stance is chosen_stance:
                continue
            summary, differences = _STANCE_PROFILE[stance]
            alternatives.append(
                AlternativeStrategy(
                    id=AlternativeId.new(),
                    stance=stance,
                    summary=summary,
                    confidence=ConfidenceScore.clamp(overall_confidence.value - 0.1),
                    key_differences=differences,
                    why_not_chosen=(
                        f"The {chosen_stance.value} stance was selected for this request."
                    ),
                )
            )
        return tuple(alternatives)
