"""Integration test: the design language grounded in the REAL Phase-13 Creative Director,
Phase-9 Psychology, Phase-8 Brand, Phase-7 Business Strategy, and Phase-3 Knowledge engines —
no fakes. The Creative Director review is itself produced over the real Phase-10/11/12 stack."""

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
    BrandContext as StBrand, GoalContext as StGoal, ProjectContext as StProject,
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
from brand.infrastructure.adapters.inmemory_inputs import InMemoryBusinessStrategyInput as BrStrategyIn
from brand.infrastructure.container import build_in_memory_environment as build_brand

# --- Phase 9: Customer Psychology Engine -----------------------------------
from psychology.application.commands import BuildPsychology
from psychology.application.contracts import RawSignal as PsySignal
from psychology.application.request import PsychologyRequest
from psychology.domain.context.context import ProjectContext as PsyProject, PsychologyBrief
from psychology.domain.shared.ids import PsychologyReportId
from psychology.domain.shared.value_objects import ProvenanceKind as PsyProv
from psychology.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput as PsyBrandIn, InMemoryBusinessStrategyInput as PsyStrategyIn,
)
from psychology.infrastructure.container import build_in_memory_environment as build_psychology

# --- Phase 10: UX Strategy Engine ------------------------------------------
from ux.application.commands import BuildUXStrategy
from ux.application.request import UXRequest
from ux.domain.context.context import ProjectContext as UXProject, UXBrief
from ux.domain.shared.ids import UXReportId
from ux.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as UXBrandIn
from ux.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as UXStrategyIn
from ux.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as UXKnowledgeIn
from ux.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as UXPsychologyIn
from ux.infrastructure.container import build_in_memory_environment as build_ux

# --- Phase 11: Information Architecture Engine -----------------------------
from ia.application.commands import BuildIA
from ia.application.request import IARequest
from ia.domain.context.context import IABrief, ProjectContext as IAProject
from ia.domain.shared.ids import IAReportId
from ia.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as IABrandIn
from ia.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as IAStrategyIn
from ia.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as IAKnowledgeIn
from ia.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as IAPsychologyIn
from ia.infrastructure.adapters.ux_input_adapter import UXInputAdapter as IAUXIn
from ia.infrastructure.container import build_in_memory_environment as build_ia

# --- Phase 12: Wireframe Planning Engine -----------------------------------
from wireframe.application.commands import BuildWireframePlan
from wireframe.application.request import WireframeRequest
from wireframe.domain.context.context import ProjectContext as WFProject, WireframeBrief
from wireframe.domain.shared.ids import WireframePlanId
from wireframe.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as WFStrategyIn
from wireframe.infrastructure.adapters.ia_input_adapter import IAInputAdapter as WFIAIn
from wireframe.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as WFKnowledgeIn
from wireframe.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as WFPsychologyIn
from wireframe.infrastructure.adapters.ux_input_adapter import UXInputAdapter as WFUXIn
from wireframe.infrastructure.container import build_in_memory_environment as build_wireframe

# --- Phase 13: Creative Director Engine ------------------------------------
from creative_director.application.commands import BuildReview
from creative_director.application.request import ReviewRequest
from creative_director.domain.context.context import ProjectContext as CDProject, ReviewSubject
from creative_director.domain.policy.policy import ReviewPolicy
from creative_director.domain.shared.ids import CreativeDirectorReviewId
from creative_director.domain.shared.value_objects import (
    ReviewMode as CDMode, ReviewProfileKind, SubjectKind,
)
from creative_director.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as CDStrategyIn
from creative_director.infrastructure.adapters.ia_input_adapter import IAInputAdapter as CDIAIn
from creative_director.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as CDKnowledgeIn
from creative_director.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as CDPsychologyIn
from creative_director.infrastructure.adapters.ux_input_adapter import UXInputAdapter as CDUXIn
from creative_director.infrastructure.adapters.wireframe_input_adapter import WireframeInputAdapter as CDWireframeIn
from creative_director.infrastructure.adapters.profiles import profile_for as cd_profile_for
from creative_director.infrastructure.container import build_in_memory_environment as build_cd

# --- Phase 14: Design Language Engine (under test) -------------------------
from design_language.application.commands import BuildDesignLanguage
from design_language.application.request import DesignLanguageRequest
from design_language.domain.context.context import DesignBrief, ProjectContext
from design_language.domain.shared.ids import DesignLanguageSpecId, DLNodeId
from design_language.domain.shared.value_objects import GraphKind, IndustryPreset
from design_language.infrastructure.adapters.brand_input_adapter import BrandInputAdapter
from design_language.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter
from design_language.infrastructure.adapters.creative_director_input_adapter import CreativeDirectorInputAdapter
from design_language.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter
from design_language.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter
from design_language.infrastructure.container import build_in_memory_environment as build_dl

from .conftest import FixedClock

pytestmark = pytest.mark.asyncio


async def _seed_knowledge(kenv, title, statement):
    view = await kenv.facade.add(AddEntry(
        category=KnowledgeCategory.CONVERSION_OPTIMIZATION, title=title, statement=statement,
        description="d", source=Source(name="NNG", kind=KSourceKind.RESEARCH_INSTITUTE),
        confidence=KConf.of(0.9), priority=KPriority.HIGH,
    ))
    vid = EntryVersionId.from_string(view.entry_version_id)
    await kenv.facade.propose(ProposeEntry(entry_version_id=vid))
    await kenv.facade.activate(ActivateEntry(entry_version_id=vid))


async def _strategy():
    senv = build_strategy(research=StResearch([
        StInsight(StProv.RESEARCH, "r1", "Customers rely on reviews and trust before buying", 0.9, tags=("trust", "review")),
        StInsight(StProv.KNOWLEDGE, "k1", "Clear value and premium restraint lift conversion", 0.85, tags=("conversion", "premium")),
    ]))
    view = await senv.facade.build(BuildStrategy(request=StrategyRequest(
        brand=StBrand(name="Aesop", industry="beauty", maturity="established", descriptors=("premium",)),
        project=StProject(project_id="proj-x", platform="shopify_plus", market="premium"),
        goals=StGoal(business_goals=("Grow retention",), user_goals=("Buy with confidence",)),
    )))
    return senv.facade, StrategyReportId.from_string(view.report_id)


async def _brand():
    benv = build_brand(business_strategy=BrStrategyIn([
        BrSignal(BrProv.BUSINESS_STRATEGY, "s1", "Position as premium apothecary value", 0.9, tags=("premium", "positioning", "brand")),
        BrSignal(BrProv.BUSINESS_STRATEGY, "s2", "Evoke restraint and craft", 0.85, tags=("restraint", "craft", "premium")),
    ]))
    view = await benv.facade.build(BuildBrand(request=BrandRequest(
        brief=BrandBrief(name="Aesop", industry="beauty skincare", maturity="established", descriptors=("premium", "minimal")),
        project=BrProject(project_id="proj-x", platform="shopify_plus", market="premium"),
    )))
    return benv.facade, BrandReportId.from_string(view.report_id)


async def _psychology():
    penv = build_psychology(
        brand=PsyBrandIn([PsySignal(PsyProv.BRAND_STRATEGY, "b1", "Evoke calm and confidence", 0.9, tags=("trust", "emotion", "calm"))]),
        business_strategy=PsyStrategyIn([PsySignal(PsyProv.BUSINESS_STRATEGY, "s1", "Premium value; restraint reassures", 0.9, tags=("premium", "trust", "restraint"))]),
    )
    view = await penv.facade.build(BuildPsychology(request=PsychologyRequest(
        brief=PsychologyBrief(product_category="skincare", price_band="premium", purchase_risk="high"),
        project=PsyProject(project_id="proj-x", platform="shopify_plus", market="premium"),
    )))
    return penv.facade, PsychologyReportId.from_string(view.report_id)


async def _ux(strategy, brand, psychology, knowledge):
    env = build_ux(psychology=UXPsychologyIn(*psychology), brand=UXBrandIn(*brand),
                   business_strategy=UXStrategyIn(*strategy), knowledge=knowledge, clock=FixedClock())
    view = await env.facade.build(BuildUXStrategy(request=UXRequest(
        brief=UXBrief(product_category="skincare"),
        project=UXProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return env.facade, UXReportId.from_string(view.report_id)


async def _ia(ux, psychology, brand, strategy, knowledge):
    env = build_ia(ux=IAUXIn(*ux), psychology=IAPsychologyIn(*psychology), brand=IABrandIn(*brand),
                   business_strategy=IAStrategyIn(*strategy), knowledge=knowledge, clock=FixedClock())
    view = await env.facade.build(BuildIA(request=IARequest(
        brief=IABrief(product_category="skincare", catalog_scale="large"),
        project=IAProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return env.facade, IAReportId.from_string(view.report_id)


async def _wireframe(ia, ux, psychology, strategy, knowledge):
    env = build_wireframe(ia=WFIAIn(*ia), ux=WFUXIn(*ux), psychology=WFPsychologyIn(*psychology),
                          business_strategy=WFStrategyIn(*strategy), knowledge=knowledge, clock=FixedClock())
    view = await env.facade.plan(BuildWireframePlan(request=WireframeRequest(
        brief=WireframeBrief(product_category="skincare", catalog_scale="large"),
        project=WFProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return env.facade, WireframePlanId.from_string(view.plan_id)


async def _creative_director(wireframe, ia, ux, strategy, psychology, knowledge):
    env = build_cd(
        wireframe=CDWireframeIn(*wireframe), ia=CDIAIn(*ia), ux=CDUXIn(*ux),
        business_strategy=CDStrategyIn(*strategy), psychology=CDPsychologyIn(*psychology),
        knowledge=knowledge, clock=FixedClock(),
    )
    subject = ReviewSubject(kind=SubjectKind.WIREFRAME_PLAN, reference=str(wireframe[1]), label="Wireframe plan")
    view = await env.facade.review(BuildReview(request=ReviewRequest(
        subject=subject, policy=ReviewPolicy(profile=cd_profile_for(ReviewProfileKind.D2C), mode=CDMode.AUTOMATIC),
        project=CDProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return env.facade, CreativeDirectorReviewId.from_string(view.review_id)


async def test_language_grounded_in_live_upstream():
    # Phase 3: seed a live knowledge corpus.
    kenv = build_knowledge()
    await _seed_knowledge(kenv, "Premium visual restraint",
                          "Modular spacing, a single type ratio, colour restraint and timelessness "
                          "define premium visual systems.")
    query = KnowledgeQueryService(kenv.repository, InMemoryKnowledgeSearchPort(kenv.storage))

    # Phases 7-13: produce the whole live upstream stack, ending in a Creative Director review.
    strategy = await _strategy()
    brand = await _brand()
    psychology = await _psychology()
    ux = await _ux(strategy, brand, psychology, UXKnowledgeIn(query))
    ia = await _ia(ux, psychology, brand, strategy, IAKnowledgeIn(query))
    wireframe = await _wireframe(ia, ux, psychology, strategy, WFKnowledgeIn(query))
    creative_director = await _creative_director(wireframe, ia, ux, strategy, psychology, CDKnowledgeIn(query))

    # Phase 14: design the visual language over the REAL upstream adapters.
    env = build_dl(
        brand=BrandInputAdapter(*brand),
        business_strategy=BusinessStrategyInputAdapter(*strategy),
        psychology=PsychologyInputAdapter(*psychology),
        creative_director=CreativeDirectorInputAdapter(*creative_director),
        knowledge=KnowledgeAdvisorAdapter(query),
        clock=FixedClock(),
    )
    view = await env.facade.design(BuildDesignLanguage(request=DesignLanguageRequest(
        brief=DesignBrief(industry=IndustryPreset.BEAUTY, tier="premium", product_category="skincare"),
        project=ProjectContext(project_id="proj-x", platform="shopify_plus", market="premium"))))

    assert view.is_production_ready
    assert view.quality.grounding == 1.0
    assert view.evidence_count > 0

    # Every visual decision must cite the live upstream — collect provenances across both graphs.
    sid = DesignLanguageSpecId.from_string(view.spec_id)
    provenances: set[str] = set()
    for kind in GraphKind:
        for node in view.graphs[kind.value]["nodes"]:
            trace = await env.facade.explain(sid, kind, DLNodeId.from_string(node["id"]))
            provenances.update(e["provenance"] for e in trace.evidence)

    assert "creative_director" in provenances
    assert "brand_strategy" in provenances
    assert "business_strategy" in provenances
    assert "psychology" in provenances
    assert "knowledge" in provenances
