"""The ReasoningEngine, driven through the facade with an in-memory advisor."""

from __future__ import annotations

from reasoning.application.commands import GenerateStrategy
from reasoning.domain.shared.ids import StrategyId
from reasoning.domain.shared.value_objects import ReasoningDimension as D


async def test_full_strategy_is_cited_and_complete(env_factory, request_pdp):
    env = env_factory()
    view = await env.facade.reason(GenerateStrategy(request=request_pdp))

    assert view.business_objective.statement == "Grow average order value."
    assert len(view.cro_principles) == 2 and len(view.problems) == 1
    assert len(view.accessibility_rules) == 1 and len(view.shopify_constraints) == 1
    assert view.typography.statement == "High-contrast serif."
    assert len(view.sections) == 2 and len(view.review_points) == 1
    # 2 structure decisions + 1 conversion decision
    assert view.evidence_count >= 15 and view.decision_count == 3


async def test_determinism(env_factory, request_pdp):
    a = await env_factory().facade.reason(GenerateStrategy(request=request_pdp))
    b = await env_factory().facade.reason(GenerateStrategy(request=request_pdp))
    assert a.confidence.overall == b.confidence.overall
    assert [s.statement for s in a.cro_principles] == [s.statement for s in b.cro_principles]


async def test_platform_constraint_becomes_critical_risk(env_factory, request_pdp):
    view = await env_factory().facade.reason(GenerateStrategy(request=request_pdp))
    assert view.risk_overall_level == "critical"
    assert any("Platform constraint" in r.description for r in view.risks)


async def test_tradeoffs_and_alternatives(env_factory, request_pdp):
    view = await env_factory().facade.reason(GenerateStrategy(request=request_pdp))
    assert len(view.tradeoffs) >= 1                        # conversion runner-up sacrificed
    assert len(view.alternatives) == 5                     # one per non-chosen stance
    assert all(a.stance != "brand_first" for a in view.alternatives)


async def test_knowledge_gap_not_fabricated(env_factory, request_pdp, full_script_dict):
    full_script_dict[D.ACCESSIBILITY] = []  # corpus silent on accessibility
    view = await env_factory(full_script_dict).facade.reason(GenerateStrategy(request=request_pdp))
    assert view.has_gaps
    assert any(g.dimension == "accessibility" for g in view.gaps)
    assert len(view.accessibility_rules) == 0             # not invented


async def test_get_and_explain(env_factory, request_pdp):
    env = env_factory()
    view = await env.facade.reason(GenerateStrategy(request=request_pdp))
    sid = StrategyId.from_string(view.strategy_id)
    again = await env.facade.get(sid)
    assert again.strategy_id == view.strategy_id
    strategy = env.storage.strategies[sid]
    decision_id = next(iter(strategy.decision_graph.nodes))
    trace = await env.facade.explain(sid, decision_id)
    assert trace.chosen and len(trace.evidence) >= 1
