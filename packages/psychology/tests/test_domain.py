"""Domain tests — the invariants that make a psychology model trustworthy by construction."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from psychology.domain.evidence.evidence import (
    EvidenceGraph,
    InvalidEvidenceError,
    PsychologyEvidence,
)
from psychology.domain.graph.psych_graph import (
    InvalidPsychGraphError,
    PsychEdge,
    PsychGraph,
    PsychNode,
)
from psychology.domain.matrices.cells import BehaviorCell
from psychology.domain.persona.jtbd import ForcesOfProgress
from psychology.domain.shared.ids import (
    MatrixCellId,
    PsychEdgeId,
    PsychNodeId,
    PsychologyEvidenceId,
)
from psychology.domain.shared.value_objects import (
    AwarenessLevel,
    Confidence,
    FeasibilityBand,
    GraphKind,
    GraphRelation,
    Intensity,
    NodeKind,
    ProvenanceKind,
    SophisticationLevel,
)

NOW = datetime(2026, 7, 14, tzinfo=UTC)


# --------------------------- value objects ------------------------------ #
def test_awareness_and_sophistication_have_five_levels_and_rank():
    assert len(AwarenessLevel) == 5 and len(SophisticationLevel) == 5
    assert AwarenessLevel.UNAWARE.rank < AwarenessLevel.MOST_AWARE.rank
    assert SophisticationLevel.STAGE_1_NEW.rank < SophisticationLevel.STAGE_5_IDENTIFICATION.rank


def test_forces_of_progress_net():
    forces = ForcesOfProgress(push=Intensity(4), pull=Intensity(4), anxiety=Intensity(2), habit=Intensity(2))
    assert forces.net_progress == 4
    assert forces.favours_switch


def test_fogg_feasibility_needs_prompt_motivation_ability():
    strong = BehaviorCell(id=MatrixCellId.new(), target_behavior="add to cart",
                          motivation=Intensity(4), ability=Intensity(4), prompt="clear CTA")
    assert strong.feasibility is FeasibilityBand.LIKELY
    no_prompt = BehaviorCell(id=MatrixCellId.new(), target_behavior="x",
                             motivation=Intensity(5), ability=Intensity(5), prompt="")
    assert no_prompt.feasibility is FeasibilityBand.UNLIKELY


# --------------------------- evidence graph ----------------------------- #
def _evidence(claim: str = "A cited fact") -> PsychologyEvidence:
    return PsychologyEvidence(
        id=PsychologyEvidenceId.new(), provenance=ProvenanceKind.BRAND_STRATEGY,
        external_ref="b1", claim=claim, confidence=Confidence.of(0.8),
    )


def test_evidence_requires_claim_and_external_ref():
    with pytest.raises(InvalidEvidenceError):
        PsychologyEvidence(
            id=PsychologyEvidenceId.new(), provenance=ProvenanceKind.KNOWLEDGE,
            external_ref="", claim="x", confidence=Confidence.of(0.5),
        )


def test_evidence_graph_rejects_duplicate_ids():
    e = _evidence()
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


# --------------------------- psych graph -------------------------------- #
def _node(kind=NodeKind.MOTIVATION, label="m") -> PsychNode:
    return PsychNode(id=PsychNodeId.new(), kind=kind, label=label)


def test_graph_rejects_dangling_edge():
    a = _node()
    edge = PsychEdge(id=PsychEdgeId.new(), source=a.id, target=PsychNodeId.new(), relation=GraphRelation.LEADS_TO)
    with pytest.raises(InvalidPsychGraphError):
        PsychGraph.of(GraphKind.MOTIVATION, [a], [edge])


def test_graph_rejects_progression_cycle():
    a, b = _node(), _node()
    edges = [
        PsychEdge(id=PsychEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.LEADS_TO),
        PsychEdge(id=PsychEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.LEADS_TO),
    ]
    with pytest.raises(InvalidPsychGraphError):
        PsychGraph.of(GraphKind.MOTIVATION, [a, b], edges)


def test_graph_allows_mutual_conflict_and_successors():
    a, b = _node(), _node(kind=NodeKind.NEED, label="need")
    edge = PsychEdge(id=PsychEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.LEADS_TO)
    graph = PsychGraph.of(GraphKind.MOTIVATION, [a, b], [edge])
    assert graph.successors(a.id) == (b,)
    assert graph.by_kind(NodeKind.NEED) == (b,)


# --------------------------- report provenance -------------------------- #
def _report(*, evidence, extra_ref=None):
    from psychology.domain.frameworks.lens import FrameworkLens
    from psychology.domain.graph.graphs import PsychologyGraphs
    from psychology.domain.journey.buying_journey import BuyingJourney, BuyingStage
    from psychology.domain.journey.decision_journey import DecisionJourney, DecisionStage
    from psychology.domain.matrices.matrices import PsychologyMatrices
    from psychology.domain.persona.buying_persona import BuyingPersonaSet
    from psychology.domain.persona.jtbd import JTBDSet
    from psychology.domain.persona.persona import PersonaSet
    from psychology.domain.quality.quality import PsychologyQualityMetrics
    from psychology.domain.report.report import CustomerPsychologyReport
    from psychology.domain.shared.ids import PsychologyReportId, PsychologyReportLineageId
    from psychology.domain.shared.value_objects import (
        CustomerIntent, DriverKind, EmotionKind, JourneyPhase, Percentage,
    )
    from psychology.domain.state.confidence import PurchaseConfidence
    from psychology.domain.state.profile import PsychologicalProfile

    ev = tuple(e.id for e in evidence)
    stage = BuyingStage(
        phase=JourneyPhase.CONSIDERATION, customer_goal="compare",
        dominant_driver=DriverKind.SOCIAL, emotion=EmotionKind.ANXIETY,
        evidence_ids=(extra_ref,) if extra_ref else ev,
    )
    profile = PsychologicalProfile(
        target_customer="considered buyer", awareness=AwarenessLevel.SOLUTION_AWARE,
        sophistication=SophisticationLevel.STAGE_3_MECHANISM, intent=CustomerIntent.COMPARING,
        confidence=PurchaseConfidence(level=Intensity(3), evidence_ids=ev),
    )
    return CustomerPsychologyReport(
        id=PsychologyReportId.new(), lineage_id=PsychologyReportLineageId.new(), version=1,
        project_id="proj", profile=profile, personas=PersonaSet(), buying_personas=BuyingPersonaSet(),
        jobs=JTBDSet(), buying_journey=BuyingJourney.of([stage]), decision_journey=DecisionJourney(),
        matrices=PsychologyMatrices(), frameworks=FrameworkLens(), graphs=PsychologyGraphs(),
        evidence_graph=EvidenceGraph.of(evidence),
        quality=PsychologyQualityMetrics(coverage=Percentage.of(1.0), grounding=Percentage.of(1.0),
                                         framework_validation=Percentage.of(1.0), confidence=Confidence.of(0.8)),
        created_at=NOW,
    )


def test_report_accepts_fully_grounded_model():
    e = _evidence()
    report = _report(evidence=[e])
    assert report.is_usable
    assert report.awareness is AwarenessLevel.SOLUTION_AWARE


def test_report_rejects_ungrounded_finding():
    from psychology.domain.report.report import InvalidPsychologyReportError

    e = _evidence()
    with pytest.raises(InvalidPsychologyReportError):
        _report(evidence=[e], extra_ref=PsychologyEvidenceId.new())  # journey stage cites missing evidence


def test_report_bundle_projection_is_neutral():
    from psychology.domain.report.bundle import UXDirectiveBundle

    e = _evidence()
    report = _report(evidence=[e])
    bundle = UXDirectiveBundle.from_report(report)
    assert bundle.awareness is AwarenessLevel.SOLUTION_AWARE
    assert bundle.report_id == report.id
    assert not bundle.is_empty
