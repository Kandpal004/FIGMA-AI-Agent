"""Domain tests — the invariants that make a UX strategy trustworthy by construction."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ux.domain.evidence.evidence import (
    EvidenceGraph,
    InvalidEvidenceError,
    UXEvidence,
)
from ux.domain.flow.flow import Flow, FlowStep, FlowTransition, InvalidFlowError
from ux.domain.graph.ux_graph import (
    InvalidUXGraphError,
    UXEdge,
    UXGraph,
    UXNode,
)
from ux.domain.page.page_strategy import InvalidPageStrategyError, PageStrategySet
from ux.domain.shared.ids import UXEdgeId, UXEvidenceId, UXNodeId
from ux.domain.shared.value_objects import (
    Confidence,
    FlowKind,
    GraphKind,
    GraphRelation,
    NodeKind,
    PageKind,
    ProvenanceKind,
    UXLaw,
)

NOW = datetime(2026, 7, 14, tzinfo=UTC)


# --------------------------- value objects ------------------------------ #
def test_ux_law_has_eleven_members():
    assert len(UXLaw) == 11


def test_page_kind_and_journey_counts():
    from ux.domain.shared.value_objects import GraphKind as GK, JourneyKind, PageKind as PK

    assert len(PK) == 9 and len(JourneyKind) == 7 and len(GK) == 5


# --------------------------- evidence graph ----------------------------- #
def _evidence(claim: str = "A cited fact") -> UXEvidence:
    return UXEvidence(
        id=UXEvidenceId.new(), provenance=ProvenanceKind.PSYCHOLOGY,
        external_ref="p1", claim=claim, confidence=Confidence.of(0.8),
    )


def test_evidence_requires_claim_and_external_ref():
    with pytest.raises(InvalidEvidenceError):
        UXEvidence(
            id=UXEvidenceId.new(), provenance=ProvenanceKind.KNOWLEDGE,
            external_ref="", claim="x", confidence=Confidence.of(0.5),
        )


def test_evidence_graph_rejects_duplicate_ids():
    e = _evidence()
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


# --------------------------- flow --------------------------------------- #
def test_flow_rejects_backward_transition():
    steps = (FlowStep(order=1, action="a"), FlowStep(order=2, action="b"))
    with pytest.raises(InvalidFlowError):
        Flow.of(FlowKind.USER, steps, (FlowTransition(2, 1),))


def test_flow_rejects_dangling_transition():
    steps = (FlowStep(order=1, action="a"),)
    with pytest.raises(InvalidFlowError):
        Flow.of(FlowKind.USER, steps, (FlowTransition(1, 3),))


# --------------------------- ux graph ----------------------------------- #
def _node(kind=NodeKind.PAGE, label="p") -> UXNode:
    return UXNode(id=UXNodeId.new(), kind=kind, label=label)


def test_graph_rejects_dangling_edge():
    a = _node()
    edge = UXEdge(id=UXEdgeId.new(), source=a.id, target=UXNodeId.new(), relation=GraphRelation.LINKS_TO)
    with pytest.raises(InvalidUXGraphError):
        UXGraph.of(GraphKind.NAVIGATION, [a], [edge])


def test_graph_rejects_containment_cycle():
    a, b = _node(), _node()
    edges = [
        UXEdge(id=UXEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.CONTAINS),
        UXEdge(id=UXEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.CONTAINS),
    ]
    with pytest.raises(InvalidUXGraphError):
        UXGraph.of(GraphKind.CONTENT_HIERARCHY, [a, b], edges)


def test_graph_allows_links_to_cycle_and_successors():
    # LINKS_TO is not a progression relation, so a mutual link is allowed.
    a, b = _node(), _node()
    edges = [
        UXEdge(id=UXEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.LINKS_TO),
        UXEdge(id=UXEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.LINKS_TO),
    ]
    graph = UXGraph.of(GraphKind.NAVIGATION, [a, b], edges)
    assert graph.successors(a.id) == (b,)


def test_page_strategy_set_rejects_duplicate_pages():
    from ux.domain.page.objective import PageObjective
    from ux.domain.page.page_strategy import PageStrategy
    from ux.domain.shared.ids import PageStrategyId

    def page():
        return PageStrategy(
            id=PageStrategyId.new(), page=PageKind.HOME,
            objective=PageObjective(statement="s", why_it_exists="w"),
        )

    with pytest.raises(InvalidPageStrategyError):
        PageStrategySet.of([page(), page()])


# --------------------------- report provenance -------------------------- #
def _report(*, evidence, extra_ref=None):
    from ux.domain.analysis.dropoff import DropoffAnalysis
    from ux.domain.analysis.friction import FrictionAnalysis
    from ux.domain.goals.goal import GoalSet, UserGoal
    from ux.domain.goals.mental_model import MentalModel
    from ux.domain.graph.graphs import UXGraphs
    from ux.domain.journey.journey import JourneyStage, UXJourney
    from ux.domain.journey.journeys import JourneyMap
    from ux.domain.laws.lens import UXLawLens
    from ux.domain.page.objective import PageObjective
    from ux.domain.page.page_strategy import PageStrategy
    from ux.domain.quality.quality import UXQualityMetrics
    from ux.domain.report.report import UXStrategyReport
    from ux.domain.shared.ids import (
        PageStrategyId,
        UserGoalId,
        UXReportId,
        UXReportLineageId,
    )
    from ux.domain.shared.value_objects import (
        JourneyKind,
        JourneyPhase,
        NavPattern,
        Percentage,
        Priority,
    )
    from ux.domain.strategy.strategies import (
        ContentStrategy,
        ErrorRecoveryStrategy,
        InteractionStrategy,
        NavigationStrategy,
        ProgressiveDisclosureStrategy,
        TrustStrategy,
        UXStrategies,
    )

    ev = tuple(e.id for e in evidence)
    goals = GoalSet.of(
        user_goals=[UserGoal(id=UserGoalId.new(), statement="buy with confidence", is_primary=True,
                             priority=Priority(5), evidence_ids=ev)],
    )
    page = PageStrategy(
        id=PageStrategyId.new(), page=PageKind.PRODUCT,
        objective=PageObjective(statement="convert", why_it_exists="drive add to cart",
                                evidence_ids=(extra_ref,) if extra_ref else ev),
    )
    strategies = UXStrategies(
        navigation=NavigationStrategy(pattern=NavPattern.FACETED),
        content=ContentStrategy(hierarchy_intent="lead with value"),
        interaction=InteractionStrategy(), error_recovery=ErrorRecoveryStrategy(),
        disclosure=ProgressiveDisclosureStrategy(), trust=TrustStrategy(),
    )
    user = UXJourney.of(JourneyKind.USER, [JourneyStage(phase=JourneyPhase.DECISION, user_goal="commit")])
    return UXStrategyReport(
        id=UXReportId.new(), lineage_id=UXReportLineageId.new(), version=1, project_id="proj",
        goals=goals, mental_model=MentalModel(summary="familiar ecommerce flow"),
        pages=PageStrategySet.of([page]), journeys=JourneyMap(user=user), flows=__import__(
            "ux.domain.flow.flow", fromlist=["FlowSet"]).FlowSet(),
        strategies=strategies, friction=FrictionAnalysis(), dropoff=DropoffAnalysis(),
        laws=UXLawLens(), graphs=UXGraphs(), evidence_graph=EvidenceGraph.of(evidence),
        quality=UXQualityMetrics(coverage=Percentage.of(1.0), grounding=Percentage.of(1.0),
                                 heuristic_validation=Percentage.of(1.0), confidence=Confidence.of(0.8)),
        created_at=NOW,
    )


def test_report_accepts_fully_grounded_strategy():
    e = _evidence()
    report = _report(evidence=[e])
    assert report.is_usable
    assert report.page_count() == 1


def test_report_rejects_ungrounded_decision():
    from ux.domain.report.report import InvalidUXReportError

    e = _evidence()
    with pytest.raises(InvalidUXReportError):
        _report(evidence=[e], extra_ref=UXEvidenceId.new())  # page objective cites missing evidence


def test_report_bundle_projection_is_neutral():
    from ux.domain.report.bundle import DesignBriefBundle

    e = _evidence()
    report = _report(evidence=[e])
    bundle = DesignBriefBundle.from_report(report)
    assert bundle.primary_user_goal == "buy with confidence"
    assert bundle.report_id == report.id
    assert not bundle.is_empty
