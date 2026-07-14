"""Integration test: brand grounded in the REAL Phase-7 Business Strategy and Phase-3
Knowledge engines — no fakes, live upstream."""

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
    BrandContext as SBrandContext,
    GoalContext as SGoalContext,
    ProjectContext as SProjectContext,
)
from strategy.domain.shared.ids import StrategyReportId
from strategy.domain.shared.value_objects import ProvenanceKind as SProvenance
from strategy.infrastructure.adapters.inmemory_inputs import (
    InMemoryResearchInput as SResearch,
)
from strategy.infrastructure.container import build_in_memory_environment as build_strategy

# --- Phase 8: Brand Strategy Engine ----------------------------------------
from brand.application.commands import BuildBrand
from brand.domain.shared.ids import BrandDecisionId, BrandReportId
from brand.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter,
)
from brand.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter
from brand.infrastructure.container import build_in_memory_environment as build_brand

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


async def _produce_strategy_report():
    """Run the real Phase-7 engine to produce a strategy, return (facade, id)."""
    insights = [
        SInsight(SProvenance.RESEARCH, "r1", "Customers rely on reviews and trust before buying", 0.9, tags=("trust", "review")),
        SInsight(SProvenance.KNOWLEDGE, "k1", "Clear value and a strong CTA lift conversion", 0.85, tags=("conversion", "value")),
        SInsight(SProvenance.COMPETITOR, "c1", "Premium rivals lead with editorial trust", 0.8, tags=("premium", "trust")),
    ]
    senv = build_strategy(research=SResearch(insights))
    request = StrategyRequest(
        brand=SBrandContext(name="Aesop", industry="beauty", maturity="established", descriptors=("premium",)),
        project=SProjectContext(project_id="proj-aesop", platform="shopify_plus", market="premium"),
        goals=SGoalContext(business_goals=("Grow retention",), user_goals=("Buy with confidence",)),
    )
    view = await senv.facade.build(BuildStrategy(request=request))
    return senv.facade, StrategyReportId.from_string(view.report_id)


@pytest.mark.asyncio
async def test_brand_grounded_in_live_strategy_and_knowledge(request_factory):
    # Phase 3: seed a live knowledge corpus (single keyword-rich principle).
    kenv = build_knowledge()
    await _author(
        kenv,
        KnowledgeCategory.TYPOGRAPHY,
        "Type conveys brand register",
        "Editorial serif typography and restrained colour convey premium, trusted brand positioning and voice.",
    )
    query_service = KnowledgeQueryService(kenv.repository, InMemoryKnowledgeSearchPort(kenv.storage))
    knowledge_adapter = KnowledgeAdvisorAdapter(query_service)

    # Phase 7: produce a live business strategy.
    strategy_facade, report_id = await _produce_strategy_report()
    strategy_adapter = BusinessStrategyInputAdapter(strategy_facade, report_id)

    # Phase 8: build the brand over the real upstream adapters.
    env = build_brand(
        business_strategy=strategy_adapter, knowledge=knowledge_adapter, clock=FixedClock()
    )
    view = await env.facade.build(BuildBrand(request=request_factory()))

    assert view.is_usable
    assert view.quality.grounding == 1.0
    assert view.evidence_count > 0

    # The brand must cite both the live business strategy and live knowledge.
    rid = BrandReportId.from_string(view.report_id)
    provenances: set[str] = set()
    for decision in view.decisions:
        trace = await env.facade.explain(rid, BrandDecisionId.from_string(decision.id))
        provenances.update(e["provenance"] for e in trace.evidence)
    assert "business_strategy" in provenances
    assert "knowledge" in provenances
