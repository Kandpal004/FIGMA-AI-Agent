"""Integration test: psychology grounded in the REAL Phase-8 Brand, Phase-7 Business
Strategy, and Phase-3 Knowledge engines — no fakes, live upstream."""

from __future__ import annotations

import pytest

# --- Phase 3: Knowledge Engine ---------------------------------------------
from knowledge.application.commands import ActivateEntry, AddEntry, ProposeEntry
from knowledge.application.query_service import KnowledgeQueryService
from knowledge.domain.entry.source import Source, SourceKind as KSourceKind
from knowledge.domain.shared.ids import EntryVersionId
from knowledge.domain.shared.value_objects import Confidence as KConf, Priority as KPriority
from knowledge.domain.taxonomy.category import KnowledgeCategory
from knowledge.infrastructure.container import build_in_memory_environment as build_knowledge
from knowledge.infrastructure.inmemory import InMemoryKnowledgeSearchPort

# --- Phase 7: Business Strategy Engine -------------------------------------
from strategy.application.commands import BuildStrategy
from strategy.application.contracts import RawInsight as SInsight
from strategy.application.request import StrategyRequest
from strategy.domain.context.context import (
    BrandContext as SBrand,
    GoalContext as SGoal,
    ProjectContext as SProject,
)
from strategy.domain.shared.ids import StrategyReportId
from strategy.domain.shared.value_objects import ProvenanceKind as SProv
from strategy.infrastructure.adapters.inmemory_inputs import InMemoryResearchInput as SResearch
from strategy.infrastructure.container import build_in_memory_environment as build_strategy

# --- Phase 8: Brand Strategy Engine ----------------------------------------
from brand.application.commands import BuildBrand
from brand.application.contracts import RawSignal as BSignal
from brand.application.request import BrandRequest
from brand.domain.context.context import BrandBrief, ProjectContext as BProject
from brand.domain.shared.ids import BrandReportId
from brand.domain.shared.value_objects import ProvenanceKind as BProv
from brand.infrastructure.adapters.inmemory_inputs import (
    InMemoryBusinessStrategyInput as BStrategyIn,
)
from brand.infrastructure.container import build_in_memory_environment as build_brand

# --- Phase 9: Customer Psychology Engine -----------------------------------
from psychology.application.commands import BuildPsychology
from psychology.domain.shared.ids import PsychNodeId, PsychologyReportId
from psychology.domain.shared.value_objects import GraphKind
from psychology.infrastructure.adapters.brand_input_adapter import BrandInputAdapter
from psychology.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter,
)
from psychology.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter
from psychology.infrastructure.container import build_in_memory_environment as build_psychology

from .conftest import FixedClock


async def _author(kenv, category, title, statement):
    view = await kenv.facade.add(
        AddEntry(
            category=category, title=title, statement=statement, description="d",
            source=Source(name="NNG", kind=KSourceKind.RESEARCH_INSTITUTE),
            confidence=KConf.of(0.9), priority=KPriority.HIGH,
        )
    )
    vid = EntryVersionId.from_string(view.entry_version_id)
    await kenv.facade.propose(ProposeEntry(entry_version_id=vid))
    await kenv.facade.activate(ActivateEntry(entry_version_id=vid))


async def _produce_strategy():
    insights = [
        SInsight(SProv.RESEARCH, "r1", "Customers rely on reviews and trust before buying", 0.9, tags=("trust", "review")),
        SInsight(SProv.KNOWLEDGE, "k1", "Clear value and a strong CTA lift conversion", 0.85, tags=("conversion", "value")),
        SInsight(SProv.COMPETITOR, "c1", "Premium rivals lead with editorial trust", 0.8, tags=("premium", "trust")),
    ]
    senv = build_strategy(research=SResearch(insights))
    req = StrategyRequest(
        brand=SBrand(name="Aesop", industry="beauty", maturity="established", descriptors=("premium",)),
        project=SProject(project_id="proj-x", platform="shopify_plus", market="premium"),
        goals=SGoal(business_goals=("Grow retention",), user_goals=("Buy with confidence",)),
    )
    view = await senv.facade.build(BuildStrategy(request=req))
    return senv.facade, StrategyReportId.from_string(view.report_id)


async def _produce_brand():
    signals = [
        BSignal(BProv.BUSINESS_STRATEGY, "s1", "Position as premium: trusted value customers commit to", 0.9, tags=("premium", "positioning", "brand")),
        BSignal(BProv.BUSINESS_STRATEGY, "s2", "Evoke trust and confidence; reviews and guarantees required", 0.85, tags=("trust", "emotion", "review", "guarantee")),
    ]
    benv = build_brand(business_strategy=BStrategyIn(signals))
    req = BrandRequest(
        brief=BrandBrief(name="Aesop", industry="beauty skincare", maturity="established", descriptors=("premium", "minimal")),
        project=BProject(project_id="proj-x", platform="shopify_plus", market="premium"),
    )
    view = await benv.facade.build(BuildBrand(request=req))
    return benv.facade, BrandReportId.from_string(view.report_id)


@pytest.mark.asyncio
async def test_psychology_grounded_in_live_upstream(request_factory):
    # Phase 3: seed a live knowledge corpus.
    kenv = build_knowledge()
    await _author(
        kenv, KnowledgeCategory.CONVERSION_OPTIMIZATION,
        "Trust drives conversion",
        "Social proof and guarantees reduce purchase anxiety and lift conversion and retention.",
    )
    query_service = KnowledgeQueryService(kenv.repository, InMemoryKnowledgeSearchPort(kenv.storage))
    knowledge_adapter = KnowledgeAdvisorAdapter(query_service)

    # Phase 7 + Phase 8: produce live strategy and brand.
    strategy_facade, strategy_id = await _produce_strategy()
    brand_facade, brand_id = await _produce_brand()

    # Phase 9: build psychology over the real upstream adapters.
    env = build_psychology(
        brand=BrandInputAdapter(brand_facade, brand_id),
        business_strategy=BusinessStrategyInputAdapter(strategy_facade, strategy_id),
        knowledge=knowledge_adapter,
        clock=FixedClock(),
    )
    view = await env.facade.build(BuildPsychology(request=request_factory()))

    assert view.is_usable
    assert view.quality.grounding == 1.0
    assert view.evidence_count > 0

    # The model must cite the live brand, business strategy, and knowledge.
    rid = PsychologyReportId.from_string(view.report_id)
    provenances: set[str] = set()
    for kind_name in ("motivation", "trust", "objection", "emotion", "behavior", "decision"):
        for node in view.graphs[kind_name]["nodes"]:
            trace = await env.facade.explain(
                rid, GraphKind(kind_name), PsychNodeId.from_string(node["id"])
            )
            provenances.update(e["provenance"] for e in trace.evidence)
    assert "brand_strategy" in provenances
    assert "business_strategy" in provenances
    assert "knowledge" in provenances
