"""Stage — Rules construction.

Derives the composition's operating rules from the coherent composition: the composition rules
(how components combine), the placement rules (which component belongs on which page and where),
the visibility rules (when each is shown/hidden), the responsive rules (how the composition
reflows), and the reuse rules (which components are shared and must stay consistent). Every rule
cites the evidence that justifies it, so the composition is reasoned, never assembled by
convention.
"""

from __future__ import annotations

from collections.abc import Sequence

from component_intelligence.domain.composition.composition import ComponentComposition
from component_intelligence.domain.evidence.evidence import CIEvidence, EvidenceGraph
from component_intelligence.domain.rules.composition_rules import (
    CompositionRule,
    CompositionRuleSet,
)
from component_intelligence.domain.rules.placement_rules import PlacementRule, PlacementRuleSet
from component_intelligence.domain.rules.responsive_rules import (
    ResponsiveCompositionRule,
    ResponsiveRuleSet,
)
from component_intelligence.domain.rules.reuse_rules import ReuseRule, ReuseRuleSet
from component_intelligence.domain.rules.visibility_rules import VisibilityRule, VisibilityRuleSet
from component_intelligence.domain.shared.ids import CIEvidenceId, RuleId
from component_intelligence.domain.shared.value_objects import (
    ComponentType,
    CompositionRuleKind,
    PlacementRegion,
    VisibilityKind,
)

__all__ = ["RulesBuilder"]

_CANON_ORDER = {c: i for i, c in enumerate(ComponentType)}

_HEADER = frozenset({
    ComponentType.ANNOUNCEMENT_BAR, ComponentType.HEADER, ComponentType.MEGA_MENU,
    ComponentType.NAVIGATION,
})
_ABOVE_FOLD = frozenset({
    ComponentType.BREADCRUMBS, ComponentType.HERO, ComponentType.HERO_CAROUSEL,
    ComponentType.PRODUCT_GALLERY, ComponentType.PRODUCT_INFORMATION, ComponentType.VARIANT_PICKER,
})
_FOOTER = frozenset({ComponentType.FOOTER, ComponentType.NEWSLETTER})
_STICKY = frozenset({ComponentType.STICKY_ADD_TO_CART})
_OVERLAY = frozenset({ComponentType.CART_DRAWER, ComponentType.MINI_CART, ComponentType.SIZE_GUIDE})


def _region(component: ComponentType) -> PlacementRegion:
    if component in _HEADER:
        return PlacementRegion.HEADER
    if component in _ABOVE_FOLD:
        return PlacementRegion.ABOVE_FOLD
    if component in _FOOTER:
        return PlacementRegion.FOOTER
    if component in _STICKY:
        return PlacementRegion.STICKY
    if component in _OVERLAY:
        return PlacementRegion.OVERLAY
    return PlacementRegion.MAIN


class RulesBuilder:
    """Derives the five rule collections from a coherent composition."""

    def build(
        self, composition: ComponentComposition, evidence: EvidenceGraph
    ) -> tuple[
        CompositionRuleSet, PlacementRuleSet, VisibilityRuleSet, ResponsiveRuleSet, ReuseRuleSet
    ]:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        return (
            self._composition_rules(ranked),
            self._placement(composition, ranked),
            self._visibility(composition, ranked),
            self._responsive(composition, ranked),
            self._reuse(composition, ranked),
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _cite(
        ranked: Sequence[CIEvidence], keywords: Sequence[str], limit: int = 1
    ) -> tuple[CIEvidenceId, ...]:
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]
        matched = [
            e for e in ranked
            if any(k in f"{e.claim} {' '.join(t.value for t in e.tags)}".lower() for k in kws)
        ]
        chosen = matched[:limit] or ranked[:1]
        return tuple(e.id for e in chosen)

    def _composition_rules(self, ranked: Sequence[CIEvidence]) -> CompositionRuleSet:
        return CompositionRuleSet.of([
            CompositionRule(id=RuleId.new(), kind=CompositionRuleKind.ORDER,
                            statement="Trust components follow the buy box; they never precede the primary action.",
                            evidence_ids=self._cite(ranked, ("trust", "conversion", "buy"))),
            CompositionRule(id=RuleId.new(), kind=CompositionRuleKind.HIERARCHY,
                            statement="Each page establishes one clear focal component.",
                            evidence_ids=self._cite(ranked, ("hierarchy", "focus", "conversion"))),
            CompositionRule(id=RuleId.new(), kind=CompositionRuleKind.GROUPING,
                            statement="Related components are grouped so intent reads at a glance.",
                            evidence_ids=self._cite(ranked, ("grouping", "structure", "ux"))),
            CompositionRule(id=RuleId.new(), kind=CompositionRuleKind.DENSITY,
                            statement="Component density follows the design language's density posture.",
                            evidence_ids=self._cite(ranked, ("density", "design", "premium", "spacing"))),
        ])

    def _placement(
        self, composition: ComponentComposition, ranked: Sequence[CIEvidence]
    ) -> PlacementRuleSet:
        rules: list[PlacementRule] = []
        for decision in composition.included():
            region = _region(decision.component)
            order = _CANON_ORDER[decision.component]
            for page in decision.usage.page_affinity:
                rules.append(PlacementRule(
                    id=RuleId.new(), component=decision.component, page=page, region=region,
                    order=order,
                    evidence_ids=self._cite(ranked, (decision.component.value, page.value, "wireframe", "structure")),
                ))
        return PlacementRuleSet.of(rules)

    def _visibility(
        self, composition: ComponentComposition, ranked: Sequence[CIEvidence]
    ) -> VisibilityRuleSet:
        rules: list[VisibilityRule] = []
        for decision in composition.included():
            component = decision.component
            if component is ComponentType.STICKY_ADD_TO_CART:
                rules.append(VisibilityRule(
                    id=RuleId.new(), component=component, kind=VisibilityKind.MOBILE_ONLY,
                    condition="Shown on mobile once the primary buy box scrolls out of view.",
                    evidence_ids=self._cite(ranked, ("mobile", "conversion", "cta"))))
            elif component is ComponentType.ANNOUNCEMENT_BAR:
                rules.append(VisibilityRule(
                    id=RuleId.new(), component=component, kind=VisibilityKind.CONDITIONAL,
                    condition="Hidden during checkout to protect focus.",
                    evidence_ids=self._cite(ranked, ("checkout", "friction", "focus"))))
            elif component is ComponentType.MEGA_MENU:
                rules.append(VisibilityRule(
                    id=RuleId.new(), component=component, kind=VisibilityKind.DESKTOP_ONLY,
                    condition="Collapses to the navigation drawer below desktop.",
                    evidence_ids=self._cite(ranked, ("navigation", "mobile", "responsive"))))
        return VisibilityRuleSet.of(rules)

    def _responsive(
        self, composition: ComponentComposition, ranked: Sequence[CIEvidence]
    ) -> ResponsiveRuleSet:
        rules: list[ResponsiveCompositionRule] = []
        for decision in composition.included():
            for rule in decision.responsive_rules:
                rules.append(ResponsiveCompositionRule(
                    id=RuleId.new(), component=decision.component, breakpoint=rule.breakpoint,
                    intent=rule.intent,
                    statement=f"{decision.component.value} {rule.intent.value}s at {rule.breakpoint.value}.",
                    evidence_ids=self._cite(ranked, (decision.component.value, "responsive", "mobile")),
                ))
        return ResponsiveRuleSet.of(rules)

    def _reuse(
        self, composition: ComponentComposition, ranked: Sequence[CIEvidence]
    ) -> ReuseRuleSet:
        rules: list[ReuseRule] = []
        for decision in composition.included():
            pages = decision.usage.page_affinity
            if len(pages) >= 2:
                rules.append(ReuseRule(
                    id=RuleId.new(), component=decision.component, shared_across=pages,
                    statement=f"{decision.component.value} is reused across pages and must stay consistent.",
                    evidence_ids=self._cite(ranked, (decision.component.value, "consistency", "reuse", "design")),
                ))
        return ReuseRuleSet.of(rules)
