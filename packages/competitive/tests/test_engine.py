"""The IntelligenceEngine, driven through the facade with in-memory ports."""

from __future__ import annotations

from competitive.application.commands import AnalyzeCompetitors
from competitive.application.ports.reasoning import StrategyDigest
from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.shared.ids import RecommendationId, ReportId
from competitive.domain.shared.value_objects import CompetitorDimension as Dim, Score
from competitive.infrastructure.inmemory import InMemoryKnowledgeAdvisor


class _Reasoning:
    async def digest(self, brief):
        return StrategyDigest(stance="conversion_first", priority_dimensions=(Dim.CONVERSION_PATTERNS,))


async def test_report_is_cited_and_complete(env_factory, full_advisor, brief):
    view = await env_factory(full_advisor).facade.analyze(AnalyzeCompetitors(brief=brief))

    # classification: Sephora is a conversion leader (score 92)
    assert any(c.name == "Sephora" and c.tier == "conversion_leader" for c in view.competitors)
    # recurring, grounded patterns -> adopt
    assert any(p.dimension == "conversion_patterns" and p.action == "adopt" for p in view.all_patterns)
    # every recommendation is evidence-backed
    assert len(view.recommendations) >= 2
    assert all(r.evidence_ids for r in view.recommendations)
    # matrices populated
    assert view.benchmark and view.gaps and view.swot and view.best_practices and view.risks
    assert view.risk_overall_level == "critical"  # conversion leader present
    assert view.is_actionable and view.version == 1


async def test_determinism(env_factory, full_advisor, brief):
    a = await env_factory(full_advisor).facade.analyze(AnalyzeCompetitors(brief=brief))
    b = await env_factory(full_advisor).facade.analyze(AnalyzeCompetitors(brief=brief))
    assert a.confidence == b.confidence
    assert len(a.recommendations) == len(b.recommendations)


async def test_strategy_digest_boosts_priority(env_factory, full_advisor, brief):
    view = await env_factory(full_advisor, reasoning=_Reasoning()).facade.analyze(
        AnalyzeCompetitors(brief=brief))
    conv_recs = [r for r in view.recommendations if r.dimension == "conversion_patterns"]
    assert any(r.priority == 4 for r in conv_recs)  # CRITICAL from priority dimension


async def test_no_opinions_when_corpus_silent(env_factory, brief):
    view = await env_factory(InMemoryKnowledgeAdvisor({})).facade.analyze(AnalyzeCompetitors(brief=brief))
    assert len(view.recommendations) == 0            # nothing grounded -> nothing recommended
    assert all(p.action != "adopt" for p in view.all_patterns)
    assert not view.is_actionable


async def test_get_and_explain(env_factory, full_advisor, brief):
    env = env_factory(full_advisor)
    view = await env.facade.analyze(AnalyzeCompetitors(brief=brief))
    rid = ReportId.from_string(view.report_id)
    assert (await env.facade.get(rid)).report_id == view.report_id
    trace = await env.facade.explain(rid, RecommendationId.from_string(view.recommendations[0].id))
    assert trace.recommendation.evidence_ids and len(trace.evidence) >= 1


async def test_versioning(env_factory, full_advisor, brief):
    env = env_factory(full_advisor)
    v1 = await env.facade.analyze(AnalyzeCompetitors(brief=brief))
    from competitive.domain.shared.ids import ReportLineageId
    lineage = ReportLineageId.from_string(v1.lineage_id)
    v2 = await env.facade.analyze(AnalyzeCompetitors(brief=brief, lineage_id=lineage))
    assert v2.version == 2 and v2.lineage_id == v1.lineage_id
    history = await env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
