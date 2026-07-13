"""Domain-layer tests: value objects, graphs, statements, and strategy integrity."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from reasoning.domain.confidence.confidence import ConfidenceBand, ConfidenceScore, StrategyConfidence
from reasoning.domain.evidence.evidence import EvidenceGraph, EvidenceRef, InvalidEvidenceError
from reasoning.domain.graph.decision import DecisionGraph, DecisionNode, DecisionOption, InvalidDecisionGraphError
from reasoning.domain.graph.reason import InvalidReasonGraphError, ReasonGraph, ReasonNode
from reasoning.domain.risk.risk import Risk, RiskAssessment, RiskCategory, RiskLevel
from reasoning.domain.shared.ids import (
    DecisionNodeId, EvidenceId, ReasonNodeId, ReasoningRunId, RiskId, StrategyId)
from reasoning.domain.shared.value_objects import (
    Likelihood, ReasoningDimension as D, Severity, StrategyStance, Weight, InvalidReasoningValueError)
from reasoning.domain.strategy.sections import (
    BusinessObjective, CompetitiveStrategy, ConversionStrategy, CustomerProfile,
    ExperienceStrategy, PlatformStrategy, ReviewStrategy, VisualStrategy)
from reasoning.domain.strategy.statement import EvidencedStatement, InvalidStatementError
from reasoning.domain.strategy.strategy import DesignStrategy, InvalidStrategyError
from reasoning.domain.strategy.structure import StructureStrategy

NOW = datetime(2026, 7, 13, tzinfo=UTC)


def _ev(dim=D.CONVERSION):
    return EvidenceRef(id=EvidenceId.new(), knowledge_id="k", entry_version_id="v", dimension=dim,
                       category="c", title="T", statement="S", source_name="src", confidence=0.85)


def test_weight_and_confidence_bands():
    assert Weight.of(0.4).scale(3).value == 1.0
    with pytest.raises(InvalidReasoningValueError):
        Weight.of(2.0)
    assert ConfidenceScore.of(0.9).band is ConfidenceBand.VERY_HIGH
    assert ConfidenceScore.clamp(1.5).value == 1.0


def test_reason_graph_is_acyclic_by_construction():
    root = ReasonNode(id=ReasonNodeId.new(), dimension=D.BUSINESS, question="q", conclusion="c", confidence=0.9)
    child = ReasonNode(id=ReasonNodeId.new(), dimension=D.CONVERSION, question="q2", conclusion="c2",
                       confidence=0.8, premise_ids=(root.id,))
    graph = ReasonGraph.of([root, child])
    assert graph.ancestors(child.id) == (root,)
    bad = ReasonNode(id=ReasonNodeId.new(), dimension=D.CONVERSION, question="q", conclusion="c",
                     confidence=0.5, premise_ids=(ReasonNodeId.new(),))
    with pytest.raises(InvalidReasonGraphError):
        ReasonGraph.of([bad])


def test_decision_requires_grounding():
    e = _ev()
    ok = DecisionNode(id=DecisionNodeId.new(), dimension=D.CONVERSION, question="q",
                      chosen=DecisionOption(label="x", evidence_ids=(e.id,)), confidence=0.8)
    assert ok.evidence_ids == (e.id,)
    with pytest.raises(InvalidDecisionGraphError):
        DecisionNode(id=DecisionNodeId.new(), dimension=D.CONVERSION, question="q",
                     chosen=DecisionOption(label="x"), confidence=0.5)


def test_statement_must_be_cited():
    e = _ev()
    EvidencedStatement(dimension=D.CONVERSION, statement="cited", evidence_ids=(e.id,), confidence=0.8)
    with pytest.raises(InvalidStatementError):
        EvidencedStatement(dimension=D.CONVERSION, statement="uncited", evidence_ids=(), confidence=0.8)


def test_risk_matrix_deterministic():
    r = Risk(id=RiskId.new(), category=RiskCategory.PLATFORM, description="d",
             severity=Severity.CRITICAL, likelihood=Likelihood.ALMOST_CERTAIN)
    assert r.score == 16 and r.level is RiskLevel.CRITICAL
    assert RiskLevel.from_score(3) is RiskLevel.LOW
    ra = RiskAssessment(risks=(r,))
    assert ra.has_critical and ra.overall_level is RiskLevel.CRITICAL


def _min_strategy(evidence_graph, **overrides):
    base = dict(
        id=StrategyId.new(), run_id=ReasoningRunId.new(), project_id="p", section_id="s",
        page_type="product", stance=StrategyStance.BALANCED,
        business=BusinessObjective(), customer=CustomerProfile(), conversion=ConversionStrategy(),
        experience=ExperienceStrategy(), platform=PlatformStrategy(), competitive=CompetitiveStrategy(),
        visual=VisualStrategy(), structure=StructureStrategy(), review=ReviewStrategy(),
        reason_graph=ReasonGraph.empty(), decision_graph=DecisionGraph.empty(),
        evidence_graph=evidence_graph, risk_assessment=RiskAssessment(),
        confidence=StrategyConfidence(overall=ConfidenceScore.of(0.8)), created_at=NOW,
    )
    base.update(overrides)
    return DesignStrategy(**base)


def test_strategy_rejects_dangling_evidence():
    orphan = _ev(D.USER_EXPERIENCE)
    bad = EvidencedStatement(dimension=D.USER_EXPERIENCE, statement="x", evidence_ids=(orphan.id,), confidence=0.8)
    with pytest.raises(InvalidStrategyError):
        _min_strategy(EvidenceGraph.empty(), experience=ExperienceStrategy(ux_principles=(bad,)))


def test_strategy_accepts_grounded_evidence():
    e = _ev(D.CONVERSION)
    st = EvidencedStatement(dimension=D.CONVERSION, statement="x", evidence_ids=(e.id,), confidence=0.85)
    strategy = _min_strategy(EvidenceGraph.of([e]), conversion=ConversionStrategy(principles=(st,)))
    assert strategy.evidence_count() == 1 and strategy.is_actionable
