"""Integration test: the information architecture grounded in the REAL Phase-10 UX Strategy,
Phase-9 Psychology, Phase-8 Brand, Phase-7 Business Strategy, and Phase-3 Knowledge engines —
no fakes, live upstream through the real input adapters."""

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
from strategy.application.contracts import RawInsight as StInsight
from strategy.application.request import StrategyRequest
from strategy.domain.context.context import (
    BrandContext as StBrand,
    GoalContext as StGoal,
    ProjectContext as StProject,
)
from strategy.domain.shared.ids import StrategyReportId
from strategy.domain.shared.value_objects import ProvenanceKind as StProv
from strategy.infrastructure.adapters.inmemory_inputs import InMemoryResearchInput as StResearch
from strategy.infrastructure.container import build_in_memory_environment as build_strategy

# --- Phase 8: Brand Strategy Engine ----------------------------------------
from brand.application.commands import BuildBrand
from brand.application.contracts import RawSignal as BrSignal
from brand.application.request import BrandRequest
from brand.domain.context.context import BrandBrief, ProjectContext as BrProject
from brand.domain.shared.ids import BrandReportId
from brand.domain.shared.value_objects import ProvenanceKind as BrProv
from brand.infrastructure.adapters.inmemory_inputs import (
    InMemoryBusinessStrategyInput as BrStrategyIn,
)
from brand.infrastructure.container import build_in_memory_environment as build_brand

# --- Phase 9: Customer Psychology Engine -----------------------------------
from psychology.application.commands import BuildPsychology
from psychology.application.contracts import RawSignal as PsySignal
from psychology.application.request import PsychologyRequest
from psychology.domain.context.context import ProjectContext as PsyProject, PsychologyBrief
from psychology.domain.shared.ids import PsychologyReportId
from psychology.domain.shared.value_objects import ProvenanceKind as PsyProv
from psychology.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput as PsyBrandIn,
    InMemoryBusinessStrategyInput as PsyStrategyIn,
)
from psychology.infrastructure.container import build_in_memory_environment as build_psychology

# --- Phase 10: UX Strategy Engine ------------------------------------------
from ux.application.commands import BuildUXStrategy
from ux.domain.shared.ids import UXReportId
from ux.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as UXBrandIn
from ux.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as UXStrategyIn,
)
from ux.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter as UXKnowledgeIn,
)
from ux.infrastructure.adapters.psychology_input_adapter import (
    PsychologyInputAdapter as UXPsychologyIn,
)
from ux.infrastructure.container import build_in_memory_environment as build_ux

# --- Phase 11: Information Architecture Engine (under test) -----------------
from ia.application.commands import BuildIA
from ia.application.request import IARequest
from ia.domain.context.context import IABrief, ProjectContext
from ia.domain.shared.ids import IAReportId
from ia.domain.shared.value_objects import GraphKind
from ia.infrastructure.adapters.brand_input_adapter import BrandInputAdapter
from ia.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter,
)
from ia.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter
from ia.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter
from ia.infrastructure.adapters.ux_input_adapter import UXInputAdapter
from ia.infrastructure.container import build_in_memory_environment as build_ia

from .conftest import FixedClock

pytestmark = pytest.mark.asyncio


async def _seed_knowledge(kenv, category, title, statement):
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
    senv = build_strategy(research=StResearch([
        StInsight(StProv.RESEARCH, "r1", "Customers rely on reviews and trust before buying", 0.9, tags=("trust", "review")),
        StInsight(StProv.KNOWLEDGE, "k1", "Clear value and CTA lift conversion", 0.85, tags=("conversion", "value")),
    ]))
    view = await senv.facade.build(BuildStrategy(request=StrategyRequest(
        brand=StBrand(name="Aesop", industry="beauty", maturity="established", descriptors=("premium",)),
        project=StProject(project_id="proj-x", platform="shopify_plus", market="premium"),
        goals=StGoal(business_goals=("Grow retention",), user_goals=("Buy with confidence",)),
    )))
    return senv.facade, StrategyReportId.from_string(view.report_id)


async def _produce_brand():
    benv = build_brand(business_strategy=BrStrategyIn([
        BrSignal(BrProv.BUSINESS_STRATEGY, "s1", "Position as premium trusted value", 0.9, tags=("premium", "positioning", "brand")),
        BrSignal(BrProv.BUSINESS_STRATEGY, "s2", "Evoke trust; reviews and guarantees required", 0.85, tags=("trust", "review", "guarantee")),
    ]))
    view = await benv.facade.build(BuildBrand(request=BrandRequest(
        brief=BrandBrief(name="Aesop", industry="beauty skincare", maturity="established", descriptors=("premium", "minimal")),
        project=BrProject(project_id="proj-x", platform="shopify_plus", market="premium"),
    )))
    return benv.facade, BrandReportId.from_string(view.report_id)


async def _produce_psychology():
    penv = build_psychology(
        brand=PsyBrandIn([PsySignal(PsyProv.BRAND_STRATEGY, "b1", "Evoke trust and confidence", 0.9, tags=("trust", "emotion"))]),
        business_strategy=PsyStrategyIn([PsySignal(PsyProv.BUSINESS_STRATEGY, "s1", "Premium value; reviews and guarantees required", 0.9, tags=("premium", "trust", "review"))]),
    )
    view = await penv.facade.build(BuildPsychology(request=PsychologyRequest(
        brief=PsychologyBrief(product_category="skincare", price_band="premium", purchase_risk="high"),
        project=PsyProject(project_id="proj-x", platform="shopify_plus", market="premium"),
    )))
    return penv.facade, PsychologyReportId.from_string(view.report_id)


async def _produce_ux(strategy, brand, psychology, knowledge):
    strategy_facade, strategy_id = strategy
    brand_facade, brand_id = brand
    psychology_facade, psychology_id = psychology
    env = build_ux(
        psychology=UXPsychologyIn(psychology_facade, psychology_id),
        brand=UXBrandIn(brand_facade, brand_id),
        business_strategy=UXStrategyIn(strategy_facade, strategy_id),
        knowledge=knowledge,
        clock=FixedClock(),
    )
    from ux.domain.context.context import ProjectContext as UXProject, UXBrief
    from ux.application.request import UXRequest

    view = await env.facade.build(BuildUXStrategy(request=UXRequest(
        brief=UXBrief(product_category="skincare"),
        project=UXProject(project_id="proj-x", platform="shopify_plus", market="premium"),
    )))
    return env.facade, UXReportId.from_string(view.report_id)


async def test_ia_grounded_in_live_upstream():
    # Phase 3: seed a live knowledge corpus of IA principles.
    kenv = build_knowledge()
    await _seed_knowledge(
        kenv, KnowledgeCategory.CONVERSION_OPTIMIZATION,
        "Faceted navigation aids large catalogs",
        "Faceted navigation, breadcrumbs, and internal linking improve findability and lift conversion.",
    )
    query = KnowledgeQueryService(kenv.repository, InMemoryKnowledgeSearchPort(kenv.storage))
    ia_knowledge = KnowledgeAdvisorAdapter(query)
    ux_knowledge = UXKnowledgeIn(query)

    # Phases 7, 8, 9, 10: produce live upstream reports.
    strategy = await _produce_strategy()
    brand = await _produce_brand()
    psychology = await _produce_psychology()
    ux = await _produce_ux(strategy, brand, psychology, ux_knowledge)

    # Phase 11: build the IA over the REAL upstream adapters.
    env = build_ia(
        ux=UXInputAdapter(*ux),
        psychology=PsychologyInputAdapter(*psychology),
        brand=BrandInputAdapter(*brand),
        business_strategy=BusinessStrategyInputAdapter(*strategy),
        knowledge=ia_knowledge,
        clock=FixedClock(),
    )
    view = await env.facade.build(BuildIA(request=IARequest(
        brief=IABrief(product_category="skincare", catalog_scale="large"),
        project=ProjectContext(project_id="proj-x", platform="shopify_plus", market="premium"),
    )))

    assert view.is_usable
    assert view.quality.grounding == 1.0
    assert view.evidence_count > 0

    # Every IA decision must cite the live upstream — collect provenances across all graphs.
    rid = IAReportId.from_string(view.report_id)
    from ia.domain.shared.ids import IANodeId

    provenances: set[str] = set()
    for kind in GraphKind:
        for node in view.graphs[kind.value]["nodes"]:
            trace = await env.facade.explain(rid, kind, IANodeId.from_string(node["id"]))
            provenances.update(e["provenance"] for e in trace.evidence)

    assert "ux_strategy" in provenances
    assert "psychology" in provenances
    assert "business_strategy" in provenances
    assert "knowledge" in provenances
