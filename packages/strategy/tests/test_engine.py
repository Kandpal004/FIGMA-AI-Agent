"""Engine tests — the strategy pipeline end to end, over in-memory persistence."""

from __future__ import annotations

import pytest

from strategy.application.commands import BuildStrategy
from strategy.domain.shared.ids import (
    StrategicDecisionId,
    StrategyReportId,
    StrategyReportLineageId,
)
from strategy.domain.shared.value_objects import ProvenanceKind

from .conftest import insight


@pytest.mark.asyncio
async def test_pipeline_produces_grounded_usable_strategy(env_factory, request_factory, insights):
    env = env_factory(insights)
    view = await env.facade.build(BuildStrategy(request=request_factory()))

    assert view.is_usable
    assert view.quality.grounding == 1.0  # every decision cites resolvable evidence
    assert view.quality.coverage == 1.0
    assert view.tier == "premium"  # derived from the premium market/descriptors
    assert view.decisions and view.priority_matrix
    # every decision is grounded — the anti-hallucination contract
    assert all(d.evidence_ids for d in view.decisions)
    assert view.evidence_count == 5


@pytest.mark.asyncio
async def test_positioning_decision_records_considered_alternatives(env_factory, request_factory, insights):
    env = env_factory(insights)
    view = await env.facade.build(BuildStrategy(request=request_factory()))
    positioning = next(d for d in view.decisions if d.type == "positioning")
    assert positioning.considered  # trade-off recorded, like a senior strategist


@pytest.mark.asyncio
async def test_tier_follows_brand_signals(env_factory, request_factory, insights):
    env = env_factory(insights)
    luxury = await env.facade.build(
        BuildStrategy(request=request_factory(market="luxury", descriptors=("luxury",)))
    )
    assert luxury.tier == "luxury"
    affordable = await env.facade.build(
        BuildStrategy(request=request_factory(market="mass", descriptors=("value",)))
    )
    assert affordable.tier == "affordable"


@pytest.mark.asyncio
async def test_pipeline_is_deterministic(env_factory, request_factory, insights):
    env = env_factory(insights)
    req = request_factory()
    a = await env.facade.build(BuildStrategy(request=req))
    b = await env.facade.build(BuildStrategy(request=req))
    assert a.quality.overall_score == b.quality.overall_score
    assert a.tier == b.tier
    assert len(a.decisions) == len(b.decisions)
    assert [i.score for i in a.priority_matrix] == [i.score for i in b.priority_matrix]


@pytest.mark.asyncio
async def test_versioning_appends_to_lineage(env_factory, request_factory, insights):
    env = env_factory(insights)
    lineage = StrategyReportLineageId.new()
    req = request_factory()
    v1 = await env.facade.build(BuildStrategy(request=req, lineage_id=lineage))
    v2 = await env.facade.build(BuildStrategy(request=req, lineage_id=lineage))
    assert v1.version == 1
    assert v2.version == 2
    history = await env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await env.facade.latest(lineage)).version == 2


@pytest.mark.asyncio
async def test_get_directive_bundle_and_explain(env_factory, request_factory, insights):
    env = env_factory(insights)
    view = await env.facade.build(BuildStrategy(request=request_factory()))
    rid = StrategyReportId.from_string(view.report_id)

    fetched = await env.facade.get(rid)
    assert fetched.report_id == view.report_id

    bundle = await env.facade.directive_bundle(rid)
    assert bundle.tier == "premium"
    assert bundle.required_trust  # design brief carries the trust directive
    assert bundle.prioritized_decisions

    positioning = next(d for d in view.decisions if d.type == "positioning")
    trace = await env.facade.explain(rid, StrategicDecisionId.from_string(positioning.id))
    assert trace.decision.id == positioning.id
    assert trace.evidence  # resolves the cited evidence


@pytest.mark.asyncio
async def test_thin_evidence_raises_evidence_gap_risk(env_factory, request_factory):
    # A single insight is below the thin-evidence threshold.
    env = env_factory([insight(ProvenanceKind.RESEARCH, "r1", "Shoppers value trust and reviews", 0.8, "trust")])
    view = await env.facade.build(BuildStrategy(request=request_factory()))
    assert any(r.category == "evidence_gap" for r in view.risks)


@pytest.mark.asyncio
async def test_no_evidence_yields_unusable_strategy(env_factory, request_factory):
    env = env_factory([])  # no insights at all
    view = await env.facade.build(BuildStrategy(request=request_factory()))
    # With no evidence, no decision can be grounded -> nothing to stand on.
    assert view.decisions == []
    assert not view.is_usable
