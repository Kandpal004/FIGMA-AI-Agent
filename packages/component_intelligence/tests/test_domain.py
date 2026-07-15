"""Unit tests for the component-intelligence domain — the invariants that make a spec trustworthy."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from component_intelligence.domain.compatibility.compatibility import (
    CompatibilityLink,
    CompatibilitySet,
    InvalidCompatibilityError,
)
from component_intelligence.domain.component.behaviour import MobileBehaviour
from component_intelligence.domain.component.decision import ComponentDecision, InvalidDecisionError
from component_intelligence.domain.component.impact import ComponentImpacts
from component_intelligence.domain.component.purpose import ComponentPurposes
from component_intelligence.domain.component.usage import UsageGuidance
from component_intelligence.domain.composition.composition import (
    ComponentComposition,
    InvalidCompositionError,
)
from component_intelligence.domain.evidence.evidence import (
    CIEvidence,
    EvidenceGraph,
    InvalidEvidenceError,
)
from component_intelligence.domain.graph.ci_graph import CIEdge, CIGraph, CINode, InvalidCIGraphError
from component_intelligence.domain.graph.graphs import ComponentGraphs
from component_intelligence.domain.quality.quality import CompositionQualityMetrics
from component_intelligence.domain.report.report import (
    ComponentCompositionSpecification,
    InvalidSpecificationError,
)
from component_intelligence.domain.rules.composition_rules import CompositionRuleSet
from component_intelligence.domain.rules.placement_rules import PlacementRule, PlacementRuleSet
from component_intelligence.domain.rules.responsive_rules import ResponsiveRuleSet
from component_intelligence.domain.rules.reuse_rules import ReuseRuleSet
from component_intelligence.domain.rules.visibility_rules import VisibilityRuleSet
from component_intelligence.domain.shared.ids import (
    CIEdgeId,
    CIEvidenceId,
    CINodeId,
    CompatibilityId,
    ComponentSpecId,
    ComponentSpecLineageId,
    DecisionId,
    RuleId,
)
from component_intelligence.domain.shared.value_objects import (
    AtomicLevel,
    CompatibilityKind,
    ComponentType,
    Confidence,
    EffectLevel,
    GraphKind,
    GraphRelation,
    Inclusion,
    NodeKind,
    PageType,
    Percentage,
    PlacementRegion,
    ProvenanceKind,
)

_NOW = datetime(2026, 7, 14, tzinfo=UTC)


def test_cardinalities() -> None:
    assert len(ComponentType) == 41
    assert len(PageType) == 10
    assert len(GraphKind) == 2


def test_evidence_graph_missing_and_duplicate() -> None:
    e = CIEvidence(id=CIEvidenceId.new(), provenance=ProvenanceKind.WIREFRAME,
                   external_ref="e1", claim="c", confidence=Confidence(0.8))
    g = EvidenceGraph.of([e])
    absent = CIEvidenceId.new()
    assert g.missing([e.id]) == () and g.missing([absent]) == (absent,)
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


def test_graph_is_acyclic() -> None:
    a = CINode(id=CINodeId.new(), kind=NodeKind.COMPONENT, label="a")
    b = CINode(id=CINodeId.new(), kind=NodeKind.COMPONENT, label="b")
    with pytest.raises(InvalidCIGraphError):
        CIGraph.of(GraphKind.DEPENDENCY, [a, b], [
            CIEdge(id=CIEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.REQUIRES),
            CIEdge(id=CIEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.REQUIRES),
        ])


def _purposes() -> ComponentPurposes:
    return ComponentPurposes(business_purpose="b", user_purpose="u",
                             conversion_purpose="c", trust_purpose="t")


def _decision(component: ComponentType, inclusion=Inclusion.INCLUDED, *, deps=(), conflicts=()) -> ComponentDecision:
    return ComponentDecision(
        id=DecisionId.new(), component=component, atomic_level=AtomicLevel.ORGANISM,
        inclusion=inclusion, purposes=_purposes(),
        impacts=ComponentImpacts(conversion_effect=EffectLevel.MODERATE),
        mobile_behaviour=MobileBehaviour("stacks"),
        usage=UsageGuidance(page_affinity=(PageType.PRODUCT,), conflicts_with=conflicts),
        dependencies=deps,
    )


def test_decision_rejects_self_dependency() -> None:
    with pytest.raises(InvalidDecisionError):
        _decision(ComponentType.HERO, deps=(ComponentType.HERO,))


def test_composition_rejects_duplicate_component() -> None:
    with pytest.raises(InvalidCompositionError):
        ComponentComposition.of([_decision(ComponentType.HERO), _decision(ComponentType.HERO)])


def test_compatibility_link_rejects_self() -> None:
    with pytest.raises(InvalidCompatibilityError):
        CompatibilityLink(id=CompatibilityId.new(), source=ComponentType.HERO,
                          target=ComponentType.HERO, kind=CompatibilityKind.REQUIRES)


def _empty_graphs() -> ComponentGraphs:
    return ComponentGraphs.of([
        CIGraph.of(GraphKind.COMPONENT, [], []),
        CIGraph.of(GraphKind.DEPENDENCY, [], []),
    ])


def _spec(composition, compatibility=None, placement=()) -> ComponentCompositionSpecification:
    return ComponentCompositionSpecification(
        id=ComponentSpecId.new(), lineage_id=ComponentSpecLineageId.new(), version=1,
        project_id="p", composition=composition,
        compatibility=compatibility or CompatibilitySet.of([]),
        composition_rules=CompositionRuleSet.of([]), placement_rules=PlacementRuleSet.of(placement),
        visibility_rules=VisibilityRuleSet.of([]), responsive_rules=ResponsiveRuleSet.of([]),
        reuse_rules=ReuseRuleSet.of([]), graphs=_empty_graphs(), evidence_graph=EvidenceGraph.empty(),
        quality=CompositionQualityMetrics(coverage=Percentage(1.0), grounding=Percentage(1.0),
                                          coherence=Percentage(1.0), confidence=Confidence(0.9)),
        created_at=_NOW,
    )


def test_coherence_rejects_conflicting_co_placed_pair() -> None:
    a = _decision(ComponentType.MINI_CART, conflicts=(ComponentType.CART_DRAWER,))
    b = _decision(ComponentType.CART_DRAWER)
    composition = ComponentComposition.of([a, b])
    placement = [
        PlacementRule(id=RuleId.new(), component=ComponentType.MINI_CART, page=PageType.PRODUCT,
                      region=PlacementRegion.OVERLAY),
        PlacementRule(id=RuleId.new(), component=ComponentType.CART_DRAWER, page=PageType.PRODUCT,
                      region=PlacementRegion.OVERLAY),
    ]
    with pytest.raises(InvalidSpecificationError):
        _spec(composition, placement=placement)


def test_coherence_rejects_dangling_dependency() -> None:
    # An included component depends on a component that is not in the composition.
    a = _decision(ComponentType.PRODUCT_GRID, deps=(ComponentType.PRODUCT_CARD,))
    composition = ComponentComposition.of([a])
    with pytest.raises(InvalidSpecificationError):
        _spec(composition)


def test_coherence_accepts_a_coherent_spec() -> None:
    a = _decision(ComponentType.PRODUCT_GRID, deps=(ComponentType.PRODUCT_CARD,))
    b = _decision(ComponentType.PRODUCT_CARD)
    spec = _spec(ComponentComposition.of([a, b]))
    assert spec.included_count() == 2


def test_quality_weighting() -> None:
    q = CompositionQualityMetrics(coverage=Percentage(0.5), grounding=Percentage(0.8),
                                  coherence=Percentage(0.4), confidence=Confidence(0.6))
    # 0.3*0.5 + 0.3*0.8 + 0.25*0.4 + 0.15*0.6 = 0.58 → 58
    assert q.overall_score.value == pytest.approx(58.0)
