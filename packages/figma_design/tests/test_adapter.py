"""Integration test: the Figma design model grounded in the REAL Phase-17 Design Orchestrator,
Phase-16 Design System, Phase-15 Component Intelligence, Phase-14 Design Language, Phase-13
Creative Director, and Phase-3 Knowledge engines — through the full P3-to-P17 stack, live."""

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

# --- Phase 8: Brand --------------------------------------------------------
from brand.application.commands import BuildBrand
from brand.application.contracts import RawSignal as BrSignal
from brand.application.request import BrandRequest
from brand.domain.context.context import BrandBrief, ProjectContext as BrProject
from brand.domain.shared.ids import BrandReportId
from brand.domain.shared.value_objects import ProvenanceKind as BrProv
from brand.infrastructure.adapters.inmemory_inputs import InMemoryBusinessStrategyInput as BrStrategyIn
from brand.infrastructure.container import build_in_memory_environment as build_brand

# --- Phase 9: Psychology ---------------------------------------------------
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

# --- Phase 10: UX ----------------------------------------------------------
from ux.application.commands import BuildUXStrategy
from ux.application.request import UXRequest
from ux.domain.context.context import ProjectContext as UXProject, UXBrief
from ux.domain.shared.ids import UXReportId
from ux.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as UXBrandIn
from ux.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as UXStrategyIn
from ux.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as UXKnowledgeIn
from ux.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as UXPsychologyIn
from ux.infrastructure.container import build_in_memory_environment as build_ux

# --- Phase 11: IA ----------------------------------------------------------
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

# --- Phase 12: Wireframe ---------------------------------------------------
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

# --- Phase 13: Creative Director -------------------------------------------
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

# --- Phase 14: Design Language ---------------------------------------------
from design_language.application.commands import BuildDesignLanguage
from design_language.application.request import DesignLanguageRequest
from design_language.domain.context.context import DesignBrief, ProjectContext as DLProject
from design_language.domain.shared.ids import DesignLanguageSpecId
from design_language.domain.shared.value_objects import IndustryPreset
from design_language.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as DLBrandIn
from design_language.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as DLStrategyIn
from design_language.infrastructure.adapters.creative_director_input_adapter import CreativeDirectorInputAdapter as DLCDIn
from design_language.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as DLKnowledgeIn
from design_language.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as DLPsychologyIn
from design_language.infrastructure.container import build_in_memory_environment as build_dl

# --- Phase 15: Component Intelligence --------------------------------------
from component_intelligence.application.commands import BuildComposition
from component_intelligence.application.request import ComponentIntelligenceRequest
from component_intelligence.domain.context.context import (
    CompositionBrief, ProjectContext as CIProject,
)
from component_intelligence.domain.shared.ids import ComponentSpecId
from component_intelligence.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as CIBrandIn
from component_intelligence.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as CIStrategyIn
from component_intelligence.infrastructure.adapters.creative_director_input_adapter import CreativeDirectorInputAdapter as CICDIn
from component_intelligence.infrastructure.adapters.design_language_input_adapter import DesignLanguageInputAdapter as CIDLIn
from component_intelligence.infrastructure.adapters.ia_input_adapter import IAInputAdapter as CIIAIn
from component_intelligence.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as CIKnowledgeIn
from component_intelligence.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as CIPsychologyIn
from component_intelligence.infrastructure.adapters.ux_input_adapter import UXInputAdapter as CIUXIn
from component_intelligence.infrastructure.adapters.wireframe_input_adapter import WireframeInputAdapter as CIWireframeIn
from component_intelligence.infrastructure.container import build_in_memory_environment as build_ci

# --- Phase 16: Design System -----------------------------------------------
from design_system.application.commands import BuildDesignSystem
from design_system.application.request import DesignSystemRequest
from design_system.domain.context.context import DesignSystemBrief, ProjectContext as DSProject
from design_system.domain.shared.ids import DesignSystemSpecId
from design_system.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as DSBrandIn
from design_system.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as DSStrategyIn
from design_system.infrastructure.adapters.component_intelligence_input_adapter import ComponentIntelligenceInputAdapter as DSCIIn
from design_system.infrastructure.adapters.creative_director_input_adapter import CreativeDirectorInputAdapter as DSCDIn
from design_system.infrastructure.adapters.design_language_input_adapter import DesignLanguageInputAdapter as DSDLIn
from design_system.infrastructure.adapters.ia_input_adapter import IAInputAdapter as DSIAIn
from design_system.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as DSKnowledgeIn
from design_system.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as DSPsychologyIn
from design_system.infrastructure.adapters.ux_input_adapter import UXInputAdapter as DSUXIn
from design_system.infrastructure.adapters.wireframe_input_adapter import WireframeInputAdapter as DSWireframeIn
from design_system.infrastructure.container import build_in_memory_environment as build_ds

# --- Phase 17: Design Orchestrator -----------------------------------------
from design_orchestrator.application.commands import BuildExecutionPlan
from design_orchestrator.application.request import OrchestrationRequest
from design_orchestrator.domain.context.context import (
    OrchestrationBrief, ProjectContext as DOProject, SourceRefs as DOSourceRefs,
)
from design_orchestrator.domain.shared.ids import DesignExecutionPlanId
from design_orchestrator.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as DOBrandIn
from design_orchestrator.infrastructure.adapters.business_strategy_input_adapter import BusinessStrategyInputAdapter as DOStrategyIn
from design_orchestrator.infrastructure.adapters.component_intelligence_input_adapter import ComponentIntelligenceInputAdapter as DOCIIn
from design_orchestrator.infrastructure.adapters.creative_director_input_adapter import CreativeDirectorInputAdapter as DOCDIn
from design_orchestrator.infrastructure.adapters.design_language_input_adapter import DesignLanguageInputAdapter as DODLIn
from design_orchestrator.infrastructure.adapters.design_system_input_adapter import DesignSystemInputAdapter as DODSIn
from design_orchestrator.infrastructure.adapters.ia_input_adapter import IAInputAdapter as DOIAIn
from design_orchestrator.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as DOKnowledgeIn
from design_orchestrator.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as DOPsychologyIn
from design_orchestrator.infrastructure.adapters.ux_input_adapter import UXInputAdapter as DOUXIn
from design_orchestrator.infrastructure.adapters.wireframe_input_adapter import WireframeInputAdapter as DOWireframeIn
from design_orchestrator.infrastructure.container import build_in_memory_environment as build_do

# --- Phase 18: Figma Design Engine (under test) ----------------------------
from figma_design.application.commands import BuildFigmaDesign
from figma_design.application.request import FigmaDesignRequest
from figma_design.domain.context.context import FigmaBrief, ProjectContext, SourceRefs
from figma_design.domain.shared.ids import FDNodeId, FigmaDesignModelId
from figma_design.domain.shared.value_objects import GraphKind
from figma_design.infrastructure.adapters.component_intelligence_input_adapter import ComponentIntelligenceInputAdapter
from figma_design.infrastructure.adapters.creative_director_input_adapter import CreativeDirectorInputAdapter
from figma_design.infrastructure.adapters.design_language_input_adapter import DesignLanguageInputAdapter
from figma_design.infrastructure.adapters.design_orchestrator_input_adapter import DesignOrchestratorInputAdapter
from figma_design.infrastructure.adapters.design_system_input_adapter import DesignSystemInputAdapter
from figma_design.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter
from figma_design.infrastructure.container import build_in_memory_environment as build_figma

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
        goals=StGoal(business_goals=("Grow retention",), user_goals=("Buy with confidence",)))))
    return senv.facade, StrategyReportId.from_string(view.report_id)


async def _brand():
    benv = build_brand(business_strategy=BrStrategyIn([
        BrSignal(BrProv.BUSINESS_STRATEGY, "s1", "Position as premium value", 0.9, tags=("premium", "positioning", "brand")),
        BrSignal(BrProv.BUSINESS_STRATEGY, "s2", "Evoke trust; reviews required", 0.85, tags=("trust", "review")),
    ]))
    view = await benv.facade.build(BuildBrand(request=BrandRequest(
        brief=BrandBrief(name="Aesop", industry="beauty skincare", maturity="established", descriptors=("premium", "minimal")),
        project=BrProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return benv.facade, BrandReportId.from_string(view.report_id)


async def _psychology():
    penv = build_psychology(
        brand=PsyBrandIn([PsySignal(PsyProv.BRAND_STRATEGY, "b1", "Evoke trust and confidence", 0.9, tags=("trust", "emotion"))]),
        business_strategy=PsyStrategyIn([PsySignal(PsyProv.BUSINESS_STRATEGY, "s1", "Premium; reviews and guarantees required", 0.9, tags=("premium", "trust", "review"))]))
    view = await penv.facade.build(BuildPsychology(request=PsychologyRequest(
        brief=PsychologyBrief(product_category="skincare", price_band="premium", purchase_risk="high"),
        project=PsyProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
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


async def _cd(wireframe, ia, ux, strategy, psychology, knowledge):
    env = build_cd(wireframe=CDWireframeIn(*wireframe), ia=CDIAIn(*ia), ux=CDUXIn(*ux),
                   business_strategy=CDStrategyIn(*strategy), psychology=CDPsychologyIn(*psychology),
                   knowledge=knowledge, clock=FixedClock())
    subject = ReviewSubject(kind=SubjectKind.WIREFRAME_PLAN, reference=str(wireframe[1]), label="Wireframe plan")
    view = await env.facade.review(BuildReview(request=ReviewRequest(
        subject=subject, policy=ReviewPolicy(profile=cd_profile_for(ReviewProfileKind.D2C), mode=CDMode.AUTOMATIC),
        project=CDProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return env.facade, CreativeDirectorReviewId.from_string(view.review_id)


async def _design_language(brand, strategy, psychology, cd, knowledge):
    env = build_dl(brand=DLBrandIn(*brand), business_strategy=DLStrategyIn(*strategy),
                   psychology=DLPsychologyIn(*psychology), creative_director=DLCDIn(*cd),
                   knowledge=knowledge, clock=FixedClock())
    view = await env.facade.design(BuildDesignLanguage(request=DesignLanguageRequest(
        brief=DesignBrief(industry=IndustryPreset.BEAUTY, tier="premium", product_category="skincare"),
        project=DLProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return env.facade, DesignLanguageSpecId.from_string(view.spec_id)


async def _component_intelligence(wireframe, ia, ux, strategy, brand, psychology, cd, dl, query):
    env = build_ci(
        wireframe=CIWireframeIn(*wireframe), ia=CIIAIn(*ia), ux=CIUXIn(*ux),
        business_strategy=CIStrategyIn(*strategy), brand=CIBrandIn(*brand),
        psychology=CIPsychologyIn(*psychology), creative_director=CICDIn(*cd),
        design_language=CIDLIn(*dl), knowledge=CIKnowledgeIn(query), clock=FixedClock(),
    )
    view = await env.facade.compose(BuildComposition(request=ComponentIntelligenceRequest(
        brief=CompositionBrief(product_category="skincare", catalog_scale="large"),
        project=CIProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return env.facade, ComponentSpecId.from_string(view.spec_id)


async def _design_system(dl, ci, cd, strategy, brand, psychology, ux, ia, wireframe, query):
    env = build_ds(
        design_language=DSDLIn(*dl), component_intelligence=DSCIIn(*ci),
        creative_director=DSCDIn(*cd), business_strategy=DSStrategyIn(*strategy),
        brand=DSBrandIn(*brand), psychology=DSPsychologyIn(*psychology), ux=DSUXIn(*ux),
        ia=DSIAIn(*ia), wireframe=DSWireframeIn(*wireframe), knowledge=DSKnowledgeIn(query),
        clock=FixedClock(),
    )
    view = await env.facade.build(BuildDesignSystem(request=DesignSystemRequest(
        brief=DesignSystemBrief(product_category="skincare"),
        project=DSProject(project_id="proj-x", platform="shopify_plus", market="premium"))))
    return env.facade, DesignSystemSpecId.from_string(view.spec_id)


async def _orchestrator(ds, ci, cd, dl, ia, ux, psychology, brand, strategy, wireframe, query):
    env = build_do(
        design_system=DODSIn(*ds), component_intelligence=DOCIIn(*ci),
        wireframe=DOWireframeIn(*wireframe), creative_director=DOCDIn(*cd),
        design_language=DODLIn(*dl), ia=DOIAIn(*ia), ux=DOUXIn(*ux),
        psychology=DOPsychologyIn(*psychology), brand=DOBrandIn(*brand),
        business_strategy=DOStrategyIn(*strategy), knowledge=DOKnowledgeIn(query), clock=FixedClock(),
    )
    view = await env.facade.orchestrate(BuildExecutionPlan(request=OrchestrationRequest(
        brief=OrchestrationBrief(product_category="skincare"),
        project=DOProject(project_id="proj-x", platform="shopify_plus", market="premium"),
        source_refs=DOSourceRefs(design_system_spec_id=str(ds[1]), component_spec_id=str(ci[1]),
                                 wireframe_plan_id=str(wireframe[1])))))
    return env.facade, DesignExecutionPlanId.from_string(view.plan_id)


async def test_figma_model_grounded_in_live_upstream():
    kenv = build_knowledge()
    await _seed_knowledge(kenv, "Professional Figma file organization",
                          "A senior designer separates a Cover, a Design System page of variables "
                          "and styles, a Components page of variant sets, and one page per "
                          "storefront page with auto-layout frames.")
    query = KnowledgeQueryService(kenv.repository, InMemoryKnowledgeSearchPort(kenv.storage))

    strategy = await _strategy()
    brand = await _brand()
    psychology = await _psychology()
    ux = await _ux(strategy, brand, psychology, UXKnowledgeIn(query))
    ia = await _ia(ux, psychology, brand, strategy, IAKnowledgeIn(query))
    wireframe = await _wireframe(ia, ux, psychology, strategy, WFKnowledgeIn(query))
    cd = await _cd(wireframe, ia, ux, strategy, psychology, CDKnowledgeIn(query))
    dl = await _design_language(brand, strategy, psychology, cd, DLKnowledgeIn(query))
    ci = await _component_intelligence(wireframe, ia, ux, strategy, brand, psychology, cd, dl, query)
    ds = await _design_system(dl, ci, cd, strategy, brand, psychology, ux, ia, wireframe, query)
    orchestrator = await _orchestrator(ds, ci, cd, dl, ia, ux, psychology, brand, strategy, wireframe, query)

    # Phase 18: model the Figma file over the REAL upstream adapters.
    env = build_figma(
        design_orchestrator=DesignOrchestratorInputAdapter(*orchestrator),
        design_system=DesignSystemInputAdapter(*ds),
        component_intelligence=ComponentIntelligenceInputAdapter(*ci),
        design_language=DesignLanguageInputAdapter(*dl),
        creative_director=CreativeDirectorInputAdapter(*cd),
        knowledge=KnowledgeAdvisorAdapter(query),
        clock=FixedClock(),
    )
    view = await env.facade.compose(BuildFigmaDesign(request=FigmaDesignRequest(
        brief=FigmaBrief(product_category="skincare"),
        project=ProjectContext(project_id="proj-x", platform="shopify_plus", market="premium"),
        source_refs=SourceRefs(execution_plan_id=str(orchestrator[1]),
                               design_system_spec_id=str(ds[1]), component_spec_id=str(ci[1])))))

    assert view.is_production_ready
    assert view.quality.grounding == 1.0
    assert view.quality.reference_integrity == 1.0
    assert view.page_count > 0
    assert view.node_count > 0
    assert view.component_set_count > 0

    mid = FigmaDesignModelId.from_string(view.model_id)
    provenances: set[str] = set()
    for kind in GraphKind:
        for node in view.graphs[kind.value]["nodes"]:
            trace = await env.facade.explain(mid, kind, FDNodeId.from_string(node["id"]))
            provenances.update(e["provenance"] for e in trace.evidence)

    assert "design_orchestrator" in provenances
    assert "design_system" in provenances
    assert "component_intelligence" in provenances
    assert "design_language" in provenances
    assert "creative_director" in provenances
    assert "knowledge" in provenances
