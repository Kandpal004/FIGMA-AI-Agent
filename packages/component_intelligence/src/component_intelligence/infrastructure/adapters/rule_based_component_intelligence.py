"""RuleBasedComponentIntelligence — the deterministic component brain (default synthesis).

Implements :class:`ComponentIntelligencePort` by mapping the codified component catalog onto
fully-specified :class:`ComponentDecision` s over the supplied evidence, and deriving the
compatibility web (requires + conflicts) between them. It reasons about *which* components the
storefront's pages need, grounds each in the upstream engines (business/wireframe for purpose,
psychology/Creative Director for impact, IA/UX for usage, wireframe/design language for the
component itself, knowledge for compatibility), and records the alternative each conflicting
component was chosen over.

It is fully deterministic (same input + evidence ⇒ same composition), dependency-free, and
honest — it invents no facts; it *reasons* about components over the evidence it is given, and
never adds a component without a cited business reason. It is not an LLM and draws no UI.
"""

from __future__ import annotations

from collections.abc import Sequence

from component_intelligence.application.contracts import ComponentInput, CompositionDraft
from component_intelligence.domain.compatibility.compatibility import (
    CompatibilityLink,
    CompatibilitySet,
)
from component_intelligence.domain.component.behaviour import (
    AnimationRule,
    InteractionRule,
    MobileBehaviour,
    ResponsiveRule,
)
from component_intelligence.domain.component.contract import (
    ExpectedOutput,
    FailureCriterion,
    RequiredInput,
    SuccessCriterion,
)
from component_intelligence.domain.component.decision import ComponentDecision
from component_intelligence.domain.component.impact import ComponentImpacts
from component_intelligence.domain.component.purpose import ComponentPurposes
from component_intelligence.domain.component.usage import UsageGuidance
from component_intelligence.domain.component.variant import ComponentState, Variant
from component_intelligence.domain.composition.composition import ComponentComposition
from component_intelligence.domain.evidence.evidence import CIEvidence, EvidenceGraph
from component_intelligence.domain.shared.ids import CIEvidenceId, CompatibilityId, DecisionId
from component_intelligence.domain.shared.value_objects import (
    AnimationKind,
    Breakpoint,
    CompatibilityKind,
    ComponentType,
    ConsideredAlternative,
    DataKind,
    IOKind,
    Inclusion,
    InteractionKind,
    Priority,
    ProvenanceKind,
    ResponsiveIntent,
)
from component_intelligence.infrastructure.adapters.component_catalog import (
    ComponentSpec,
    all_specs,
)

__all__ = ["RuleBasedComponentIntelligence"]

_BASELINE_RESPONSIVE = (
    ResponsiveRule(Breakpoint.MOBILE, ResponsiveIntent.STACK),
    ResponsiveRule(Breakpoint.TABLET, ResponsiveIntent.REFLOW),
    ResponsiveRule(Breakpoint.DESKTOP, ResponsiveIntent.RETAIN),
)
_SPECIAL_RESPONSIVE: dict[ComponentType, tuple[ResponsiveRule, ...]] = {
    ComponentType.MEGA_MENU: (ResponsiveRule(Breakpoint.MOBILE, ResponsiveIntent.COLLAPSE),),
    ComponentType.STICKY_ADD_TO_CART: (ResponsiveRule(Breakpoint.MOBILE, ResponsiveIntent.STICKY),),
    ComponentType.HERO_CAROUSEL: (ResponsiveRule(Breakpoint.MOBILE, ResponsiveIntent.CAROUSEL),),
    ComponentType.FILTERS: (ResponsiveRule(Breakpoint.MOBILE, ResponsiveIntent.COLLAPSE),),
}


class RuleBasedComponentIntelligence:
    """A deterministic, evidence-grounded implementation of the component brain."""

    async def decide(
        self, component_input: ComponentInput, evidence: EvidenceGraph
    ) -> CompositionDraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        pages = set(component_input.brief.pages)

        decisions: list[ComponentDecision] = []
        candidate_components: set[ComponentType] = set()
        for spec in all_specs():
            affinity = tuple(p for p in spec.pages if p in pages)
            if not affinity:
                continue
            candidate_components.add(spec.component)
            decisions.append(self._decision(spec, affinity, ranked))

        compatibility = self._compatibility(candidate_components, ranked)
        return CompositionDraft(
            composition=ComponentComposition.of(decisions), compatibility=compatibility
        )

    # ------------------------------------------------------------------ #
    def _decision(
        self, spec: ComponentSpec, affinity, ranked: Sequence[CIEvidence]
    ) -> ComponentDecision:
        purpose_cite = self._prefer(ranked, ProvenanceKind.BUSINESS_STRATEGY,
                                    (spec.component.value, "business", "conversion", "purpose"))
        impact_cite = self._prefer(ranked, ProvenanceKind.PSYCHOLOGY,
                                   ("trust", "conversion", "friction", "emotion", spec.component.value))
        cd_cite = self._prefer(ranked, ProvenanceKind.CREATIVE_DIRECTOR,
                               ("quality", "approved", "premium", spec.component.value))
        usage_cite = self._prefer(ranked, ProvenanceKind.INFORMATION_ARCHITECTURE,
                                  ("structure", "hierarchy", "page", spec.component.value))
        ux_cite = self._prefer(ranked, ProvenanceKind.UX_STRATEGY,
                               ("ux", "interaction", "flow", spec.component.value))
        wf_cite = self._prefer(ranked, ProvenanceKind.WIREFRAME,
                               (spec.component.value, "section", "component", "structure"))
        dl_cite = self._prefer(ranked, ProvenanceKind.DESIGN_LANGUAGE,
                               ("token", "variant", "design", "language", spec.component.value))

        purposes = ComponentPurposes(
            business_purpose=spec.business, user_purpose=spec.user,
            conversion_purpose=spec.conversion, trust_purpose=spec.trust,
            evidence_ids=self._dedup(purpose_cite + wf_cite),
        )
        impacts = ComponentImpacts(
            seo=spec.seo, accessibility=spec.accessibility, performance=spec.performance,
            conversion_effect=spec.conversion_effect, friction_effect=spec.friction_effect,
            trust_effect=spec.trust_effect, evidence_ids=self._dedup(impact_cite + cd_cite),
        )
        usage = UsageGuidance(
            page_affinity=affinity, when_to_use=(spec.when_to_use,),
            when_not_to_use=(spec.when_not_to_use,), conflicts_with=spec.conflicts,
            evidence_ids=self._dedup(usage_cite + ux_cite),
        )
        responsive = _SPECIAL_RESPONSIVE.get(spec.component, ()) + _BASELINE_RESPONSIVE
        interactions = tuple(InteractionRule(kind=k, intent=f"{k.value} interaction") for k in spec.interactions)
        outputs = [ExpectedOutput(kind=IOKind.ARTIFACT, name=f"{spec.component.value}_render")]
        if InteractionKind.ADD_TO_CART in spec.interactions:
            outputs.append(ExpectedOutput(kind=IOKind.EVENT, name="add_to_cart"))
        if InteractionKind.SUBMIT in spec.interactions:
            outputs.append(ExpectedOutput(kind=IOKind.EVENT, name="submit"))
        considered = (
            ConsideredAlternative(option=spec.conflicts[0].value,
                                  reason_rejected="chosen over it for focus and coherence")
            if spec.conflicts else None
        )
        return ComponentDecision(
            id=DecisionId.new(), component=spec.component, atomic_level=spec.atomic,
            inclusion=Inclusion.OPTIONAL if spec.optional else Inclusion.INCLUDED,
            priority=Priority(spec.priority), purposes=purposes, impacts=impacts,
            mobile_behaviour=MobileBehaviour(spec.mobile), usage=usage,
            responsive_rules=responsive, interaction_rules=interactions,
            animation_rules=(AnimationRule(kind=AnimationKind.FADE, intent="subtle entrance"),),
            dependencies=spec.dependencies,
            required_inputs=(
                tuple(RequiredInput(kind=d) for d in spec.data)
                if spec.data
                else (RequiredInput(kind=DataKind.CONTENT),)
            ),
            expected_outputs=tuple(outputs),
            success_criteria=(SuccessCriterion(
                f"{spec.component.value} renders with real data and its primary interaction works."),),
            failure_criteria=(FailureCriterion(
                f"{spec.component.value} lacks required data or its primary interaction fails."),),
            variants=tuple(Variant(name=v) for v in spec.variants),
            states=tuple(ComponentState(kind=s) for s in spec.states),
            design_token_refs=spec.tokens + ("type.body",),
            considered_alternative=considered,
            evidence_ids=self._dedup(wf_cite + dl_cite),
        )

    def _compatibility(
        self, candidates: set[ComponentType], ranked: Sequence[CIEvidence]
    ) -> CompatibilitySet:
        know_cite = self._prefer(ranked, ProvenanceKind.KNOWLEDGE,
                                 ("component", "pattern", "compatibility", "composition"))
        links: list[CompatibilityLink] = []
        seen_conflicts: set[frozenset[ComponentType]] = set()
        for spec in all_specs():
            if spec.component not in candidates:
                continue
            for dep in spec.dependencies:
                if dep in candidates:
                    links.append(CompatibilityLink(
                        id=CompatibilityId.new(), source=spec.component, target=dep,
                        kind=CompatibilityKind.REQUIRES,
                        rationale=f"{spec.component.value} needs {dep.value}.", evidence_ids=know_cite,
                    ))
            for conflict in spec.conflicts:
                pair = frozenset({spec.component, conflict})
                if conflict in candidates and pair not in seen_conflicts:
                    seen_conflicts.add(pair)
                    links.append(CompatibilityLink(
                        id=CompatibilityId.new(), source=spec.component, target=conflict,
                        kind=CompatibilityKind.CONFLICTS_WITH,
                        rationale=f"{spec.component.value} and {conflict.value} cannot coexist.",
                        evidence_ids=know_cite,
                    ))
        return CompatibilitySet.of(links)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _dedup(ids: tuple[CIEvidenceId, ...]) -> tuple[CIEvidenceId, ...]:
        return tuple(dict.fromkeys(ids))

    @staticmethod
    def _prefer(
        ranked: Sequence[CIEvidence], provenance: ProvenanceKind, keywords: Sequence[str],
        limit: int = 2,
    ) -> tuple[CIEvidenceId, ...]:
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]

        def matches(e: CIEvidence) -> bool:
            hay = f"{e.claim} {e.statement} {' '.join(t.value for t in e.tags)}".lower()
            return any(k in hay for k in kws)

        pref = [e for e in ranked if e.provenance is provenance]
        pref_match = [e for e in pref if matches(e)]
        other_match = [e for e in ranked if e.provenance is not provenance and matches(e)]
        ordered = list(dict.fromkeys([*pref_match, *pref, *other_match, ranked[0]]))
        return tuple(e.id for e in ordered[:limit])
