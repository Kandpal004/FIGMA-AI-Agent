"""Domain tests — the invariants that make a strategy trustworthy by construction."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from strategy.domain.analysis.opportunity import OpportunityRegister
from strategy.domain.analysis.risk import BusinessRisk, RiskRegister
from strategy.domain.customer.icp import IdealCustomerProfile
from strategy.domain.customer.model import CustomerModel
from strategy.domain.decision.decision import StrategicDecision
from strategy.domain.decision.decision_graph import (
    DecisionEdge,
    DecisionGraph,
    InvalidDecisionGraphError,
)
from strategy.domain.decision.strategy_graph import StrategyGraph
from strategy.domain.evidence.evidence import (
    EvidenceGraph,
    InvalidEvidenceError,
    StrategyEvidence,
)
from strategy.domain.goals.business_goal import BusinessGoal, GoalSet
from strategy.domain.messaging.brand_voice import BrandPersonality, BrandVoice
from strategy.domain.messaging.messaging import MessagingFramework
from strategy.domain.positioning.positioning import (
    BrandPositioning,
    CustomerPositioning,
    PositioningStrategy,
    VisualPositioning,
)
from strategy.domain.positioning.tier import PositioningStatement
from strategy.domain.pricing.pricing import PricingStrategy
from strategy.domain.prioritization.priority_matrix import (
    PrioritizedItem,
    PriorityMatrix,
)
from strategy.domain.quality.quality import StrategyQualityMetrics
from strategy.domain.report.report import (
    BusinessStrategyReport,
    InvalidStrategyReportError,
)
from strategy.domain.retention.retention import RetentionStrategy
from strategy.domain.shared.ids import (
    BusinessGoalId,
    DecisionEdgeId,
    PrioritizedItemId,
    StrategicDecisionId,
    StrategyEvidenceId,
    StrategyReportId,
    StrategyReportLineageId,
)
from strategy.domain.shared.value_objects import (
    Confidence,
    DecisionRelation,
    DecisionType,
    EffortScore,
    GoalCategory,
    GoalHorizon,
    ImpactScore,
    MessagingTone,
    Percentage,
    PricingPosture,
    Priority,
    PriorityQuadrant,
    ProvenanceKind,
    ReachScore,
    StrategyTier,
)
from strategy.domain.trust.trust import TrustStrategy
from strategy.domain.value.usp import UniqueSellingProposition
from strategy.domain.value.value_proposition import ValueProposition

NOW = datetime(2026, 7, 14, tzinfo=UTC)


# --------------------------- value objects ------------------------------ #
def test_strategy_tier_has_six_members():
    assert len(StrategyTier) == 6


def test_priority_rejects_out_of_range():
    from strategy.domain.shared.value_objects import InvalidStrategyValueError

    with pytest.raises(InvalidStrategyValueError):
        Priority(6)


def test_money_rejects_negative_and_normalises_currency():
    from strategy.domain.shared.value_objects import InvalidStrategyValueError, Money

    with pytest.raises(InvalidStrategyValueError):
        Money(-1.0, "USD")
    assert Money(10.0, "usd").currency == "USD"


# --------------------------- evidence graph ----------------------------- #
def _evidence(claim: str = "A cited fact") -> StrategyEvidence:
    return StrategyEvidence(
        id=StrategyEvidenceId.new(),
        provenance=ProvenanceKind.RESEARCH,
        external_ref="r1",
        claim=claim,
        confidence=Confidence.of(0.8),
    )


def test_evidence_requires_claim_and_external_ref():
    with pytest.raises(InvalidEvidenceError):
        StrategyEvidence(
            id=StrategyEvidenceId.new(), provenance=ProvenanceKind.RESEARCH,
            external_ref="", claim="x", confidence=Confidence.of(0.5),
        )


def test_evidence_graph_rejects_duplicate_ids():
    e = _evidence()
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


# --------------------------- decision graph ----------------------------- #
def _decision(evidence_ids=(), decision_type=DecisionType.POSITIONING) -> StrategicDecision:
    return StrategicDecision(
        id=StrategicDecisionId.new(),
        type=decision_type,
        title="Position as premium",
        statement="Commit to a premium position.",
        confidence=Confidence.of(0.8),
        priority=Priority(5),
        evidence_ids=tuple(evidence_ids),
    )


def test_decision_graph_rejects_dangling_edge():
    a = _decision()
    edge = DecisionEdge(
        id=DecisionEdgeId.new(), source=a.id, target=StrategicDecisionId.new(),
        relation=DecisionRelation.SUPPORTS,
    )
    with pytest.raises(InvalidDecisionGraphError):
        DecisionGraph.of([a], [edge])


def test_decision_graph_rejects_derives_from_cycle():
    a, b = _decision(), _decision()
    edges = [
        DecisionEdge(id=DecisionEdgeId.new(), source=a.id, target=b.id, relation=DecisionRelation.DERIVES_FROM),
        DecisionEdge(id=DecisionEdgeId.new(), source=b.id, target=a.id, relation=DecisionRelation.DERIVES_FROM),
    ]
    with pytest.raises(InvalidDecisionGraphError):
        DecisionGraph.of([a, b], edges)


def test_decision_graph_allows_mutual_conflict():
    a, b = _decision(), _decision()
    edges = [
        DecisionEdge(id=DecisionEdgeId.new(), source=a.id, target=b.id, relation=DecisionRelation.CONFLICTS_WITH),
        DecisionEdge(id=DecisionEdgeId.new(), source=b.id, target=a.id, relation=DecisionRelation.CONFLICTS_WITH),
    ]
    graph = DecisionGraph.of([a, b], edges)
    assert len(graph.conflicts()) == 2


# --------------------------- priority matrix ---------------------------- #
def test_prioritized_item_scoring_and_quadrant():
    item = PrioritizedItem(
        id=PrioritizedItemId.new(), decision_id=StrategicDecisionId.new(), title="t",
        reach=ReachScore(5), impact=ImpactScore(5), confidence=Confidence.of(1.0),
        effort=EffortScore(2),
    )
    assert item.score == 12.5  # 5*5*1.0 / 2
    assert item.quadrant is PriorityQuadrant.QUICK_WIN


# --------------------------- report provenance -------------------------- #
def _report(*, decisions, evidence, priority_items=()) -> BusinessStrategyReport:
    goal = BusinessGoal(
        id=BusinessGoalId.new(), statement="Grow revenue", category=GoalCategory.REVENUE,
        horizon=GoalHorizon.MID_TERM, priority=Priority(5),
        evidence_ids=tuple(e.id for e in evidence),
    )
    positioning = PositioningStrategy(
        statement=PositioningStatement(
            tier=StrategyTier.PREMIUM, for_customer="premium shoppers", need="buy with confidence",
            category="Acme is a premium brand", benefit="trusted value", confidence=Confidence.of(0.8),
            evidence_ids=tuple(e.id for e in evidence),
        ),
        brand=BrandPositioning(perception="trusted premium"),
        customer=CustomerPositioning(current_alternative="cheaper rivals", desired_shift="pay for trust"),
        visual=VisualPositioning(tier=StrategyTier.PREMIUM, adjectives=("refined",)),
    )
    return BusinessStrategyReport(
        id=StrategyReportId.new(),
        lineage_id=StrategyReportLineageId.new(),
        version=1,
        project_id="proj",
        goals=GoalSet.of([goal]),
        customer=CustomerModel(icp=IdealCustomerProfile(summary="considered buyers")),
        positioning=positioning,
        value_proposition=ValueProposition(headline_promise="Trust delivered", primary_benefit="confidence"),
        usp=UniqueSellingProposition(statement="Most trusted in category"),
        messaging=MessagingFramework.build("Buy with confidence"),
        brand_voice=BrandVoice(tone=MessagingTone.AUTHORITATIVE),
        brand_personality=BrandPersonality(),
        trust=TrustStrategy(),
        pricing=PricingStrategy(posture=PricingPosture.PREMIUM),
        retention=RetentionStrategy(),
        decision_graph=DecisionGraph.of(decisions),
        strategy_graph=StrategyGraph.empty(),
        priority_matrix=PriorityMatrix.of(priority_items),
        risk_register=RiskRegister(),
        opportunity_register=OpportunityRegister(),
        evidence_graph=EvidenceGraph.of(evidence),
        quality=StrategyQualityMetrics(
            coverage=Percentage.of(1.0), grounding=Percentage.of(1.0),
            confidence=Confidence.of(0.8), completeness=Percentage.of(1.0),
        ),
        created_at=NOW,
    )


def test_report_accepts_fully_grounded_strategy():
    e = _evidence()
    report = _report(decisions=[_decision(evidence_ids=[e.id])], evidence=[e])
    assert report.is_usable
    assert report.tier is StrategyTier.PREMIUM


def test_report_rejects_ungrounded_decision():
    e = _evidence()
    rogue = _decision(evidence_ids=[StrategyEvidenceId.new()])  # cites missing evidence
    with pytest.raises(InvalidStrategyReportError):
        _report(decisions=[rogue], evidence=[e])


def test_report_rejects_priority_referencing_unknown_decision():
    e = _evidence()
    item = PrioritizedItem(
        id=PrioritizedItemId.new(), decision_id=StrategicDecisionId.new(), title="t",
        reach=ReachScore(3), impact=ImpactScore(3), confidence=Confidence.of(0.5), effort=EffortScore(3),
    )
    with pytest.raises(InvalidStrategyReportError):
        _report(decisions=[_decision(evidence_ids=[e.id])], evidence=[e], priority_items=[item])


def test_report_bundle_projection_is_neutral():
    from strategy.domain.report.bundle import DesignDirectiveBundle

    e = _evidence()
    d = _decision(evidence_ids=[e.id])
    item = PrioritizedItem(
        id=PrioritizedItemId.new(), decision_id=d.id, title=d.title,
        reach=ReachScore(5), impact=ImpactScore(5), confidence=Confidence.of(0.8), effort=EffortScore(3),
    )
    report = _report(decisions=[d], evidence=[e], priority_items=[item])
    bundle = DesignDirectiveBundle.from_report(report)
    assert bundle.tier is StrategyTier.PREMIUM
    assert bundle.report_id == report.id
    assert not bundle.is_empty
    assert len(bundle.prioritized_decisions) == 1
