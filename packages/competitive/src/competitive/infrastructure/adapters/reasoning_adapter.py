"""ReasoningAdapter — optional alignment with a Phase-4 design strategy.

Per the approved decision, the Reasoning Engine is an *optional* input. This adapter
implements the :class:`ReasoningPort` over an already-produced Phase-4 design
strategy view: it projects the strategy's stance and its highest-confidence
dimensions into a :class:`StrategyDigest`, mapping Phase-4 reasoning dimensions to
this engine's competitor dimensions. The intelligence engine uses the digest only to
bias recommendation priority — it never affects grounding, which stays Knowledge-only.

The caller supplies the strategy view (obtained by running Phase 4 for the relevant
section); this adapter does not itself invoke Phase 4, keeping the coupling loose and
the mapping explicit.
"""

from __future__ import annotations

from reasoning.interfaces.dto import DesignStrategyView

from competitive.application.ports.reasoning import StrategyDigest
from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.shared.value_objects import CompetitorDimension as Dim

__all__ = ["ReasoningAdapter"]

# Phase-4 reasoning dimension value → this engine's competitor dimension.
_REASONING_TO_COMPETITIVE: dict[str, Dim] = {
    "conversion": Dim.CONVERSION_PATTERNS,
    "user_experience": Dim.NAVIGATION,
    "accessibility": Dim.ACCESSIBILITY,
    "typography": Dim.TYPOGRAPHY,
    "spacing": Dim.SPACING,
    "visual_hierarchy": Dim.VISUAL_LANGUAGE,
    "design_system": Dim.VISUAL_LANGUAGE,
    "structure": Dim.HOMEPAGE_STRUCTURE,
    "trust_mechanisms": Dim.TRUST_STRATEGY,
    "business": Dim.BRAND_POSITIONING,
}

_PRIORITY_THRESHOLD = 0.7


class ReasoningAdapter:
    """Implements :class:`ReasoningPort` over a Phase-4 design strategy view."""

    def __init__(self, strategy_view: DesignStrategyView) -> None:
        self._view = strategy_view

    async def digest(self, brief: CompetitiveBrief) -> StrategyDigest:
        priorities: list[Dim] = []
        for dimension_value, confidence in self._view.confidence.by_dimension.items():
            if confidence < _PRIORITY_THRESHOLD:
                continue
            mapped = _REASONING_TO_COMPETITIVE.get(dimension_value)
            if mapped is not None and mapped not in priorities:
                priorities.append(mapped)
        return StrategyDigest(
            stance=self._view.stance,
            priority_dimensions=tuple(priorities),
            notes="aligned with the active design strategy",
        )
