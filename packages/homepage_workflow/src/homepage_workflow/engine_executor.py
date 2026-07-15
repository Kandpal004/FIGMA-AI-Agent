"""The engine executor — the single seam where the workflow runs the real engines.

The Director decides *what* runs next; this :class:`EngineAgentExecutor` is *how* each step's work
actually happens. It implements the Director's :class:`~director.application.ports.agent_executor_port.AgentExecutorPort`
and, for each step, invokes the **real** production engine (Phases 3, 5–18) through its existing
facade, wiring every engine to its true upstream inputs with the platform's real input adapters —
exactly as the live integration tests do. Nothing here reimplements a design decision; the executor
only *sequences* engines and threads their outputs through a per-run :class:`RunContext`.

Each ``execute`` returns a normalized :class:`AgentExecutionResult`: ``OK`` with the produced
artifact ids and a one-line reasoning summary; ``REJECTED`` (from the Creative Director review gate)
with the concrete changes required; or ``FAILED`` with an error so the Director's retry policy
engages. The two Creative-Director gates give the workflow its self-correcting spine — the wireframe
review rewinds to UX on rejection, and the final-approval gate rewinds to self-improvement.

Engines run over in-memory persistence (the whole platform's local mode); the *engine logic* is the
real production logic. This module imports the engines (an infrastructure concern) but the Director,
which depends only on the port, never sees them.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from director.application.ports.agent_executor_port import (
    AgentExecutionRequest,
    AgentExecutionResult,
    AgentExecutorPort,
    ExecutionStatus,
)
from director.domain.shared.ids import RunId

from homepage_workflow import definition as wf
from homepage_workflow.request import HomepageRequest
from homepage_workflow.run_context import HomepageBrief, RunContext
from homepage_workflow.section_plan import HOMEPAGE_SECTIONS, ApprovalStatus, HomepageDesignPlan
from homepage_workflow.section_projection import meets_bar, project_section, score_section

# --- Phase 6: Research ------------------------------------------------------ #
from research.application.commands import Research
from research.domain.shared.ids import ResearchReportId
from research.domain.source.request import ResearchRequest
from research.infrastructure.container import build_in_memory_environment as build_research

# --- Phase 5: Competitive Intelligence -------------------------------------- #
from competitive.application.commands import AnalyzeCompetitors
from competitive.application.ports.knowledge_advisor import AdvisedPrinciple
from competitive.domain.competitor.competitor import Competitor
from competitive.domain.competitor.observation import Observation, ObservationSet
from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.shared.ids import CompetitorId, ObservationId, ReportId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Confidence as CompConfidence,
    ObservationSource,
    Score as CompScore,
)
from competitive.infrastructure.container import build_in_memory_environment as build_competitive
from competitive.infrastructure.inmemory import InMemoryDataSource, InMemoryKnowledgeAdvisor

# --- Phase 7: Business Strategy --------------------------------------------- #
from strategy.application.commands import BuildStrategy
from strategy.application.request import StrategyRequest
from strategy.domain.context.context import (
    BrandContext as StBrand,
    GoalContext as StGoal,
    ProjectContext as StProject,
)
from strategy.domain.shared.ids import StrategyReportId
from strategy.infrastructure.adapters.research_input_adapter import (
    ResearchInputAdapter as StResearchIn,
)
from strategy.infrastructure.container import build_in_memory_environment as build_strategy

# --- Phase 8: Brand --------------------------------------------------------- #
from brand.application.commands import BuildBrand
from brand.application.request import BrandRequest
from brand.domain.context.context import BrandBrief, ProjectContext as BrProject
from brand.domain.shared.ids import BrandReportId
from brand.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as BrStrategyIn,
)
from brand.infrastructure.container import build_in_memory_environment as build_brand

# --- Phase 9: Psychology ---------------------------------------------------- #
from psychology.application.commands import BuildPsychology
from psychology.application.request import PsychologyRequest
from psychology.domain.context.context import ProjectContext as PsyProject, PsychologyBrief
from psychology.domain.shared.ids import PsychologyReportId
from psychology.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as PsyBrandIn
from psychology.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as PsyStrategyIn,
)
from psychology.infrastructure.container import build_in_memory_environment as build_psychology

# --- Phase 10: UX ----------------------------------------------------------- #
from ux.application.commands import BuildUXStrategy
from ux.application.request import UXRequest
from ux.domain.context.context import ProjectContext as UXProject, UXBrief
from ux.domain.shared.ids import UXReportId
from ux.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as UXBrandIn
from ux.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as UXStrategyIn,
)
from ux.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as UXKnowIn
from ux.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as UXPsyIn
from ux.infrastructure.container import build_in_memory_environment as build_ux

# --- Phase 11: IA ----------------------------------------------------------- #
from ia.application.commands import BuildIA
from ia.application.request import IARequest
from ia.domain.context.context import IABrief, ProjectContext as IAProject
from ia.domain.shared.ids import IAReportId
from ia.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as IABrandIn
from ia.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as IAStrategyIn,
)
from ia.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter as IAKnowIn
from ia.infrastructure.adapters.psychology_input_adapter import PsychologyInputAdapter as IAPsyIn
from ia.infrastructure.adapters.ux_input_adapter import UXInputAdapter as IAUXIn
from ia.infrastructure.container import build_in_memory_environment as build_ia

# --- Phase 12: Wireframe ---------------------------------------------------- #
from wireframe.application.commands import BuildWireframePlan
from wireframe.application.request import WireframeRequest
from wireframe.domain.context.context import ProjectContext as WFProject, WireframeBrief
from wireframe.domain.shared.ids import WireframePlanId
from wireframe.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as WFStrategyIn,
)
from wireframe.infrastructure.adapters.ia_input_adapter import IAInputAdapter as WFIAIn
from wireframe.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter as WFKnowIn,
)
from wireframe.infrastructure.adapters.psychology_input_adapter import (
    PsychologyInputAdapter as WFPsyIn,
)
from wireframe.infrastructure.adapters.ux_input_adapter import UXInputAdapter as WFUXIn
from wireframe.infrastructure.container import build_in_memory_environment as build_wireframe

# --- Phase 13: Creative Director -------------------------------------------- #
from creative_director.application.commands import BuildReview
from creative_director.application.request import ReviewRequest
from creative_director.domain.context.context import ProjectContext as CDProject, ReviewSubject
from creative_director.domain.policy.policy import ReviewPolicy
from creative_director.domain.shared.ids import CreativeDirectorReviewId
from creative_director.domain.shared.value_objects import (
    ReviewMode as CDMode,
    ReviewProfileKind,
    SubjectKind,
)
from creative_director.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as CDStrategyIn,
)
from creative_director.infrastructure.adapters.ia_input_adapter import IAInputAdapter as CDIAIn
from creative_director.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter as CDKnowIn,
)
from creative_director.infrastructure.adapters.profiles import profile_for as cd_profile_for
from creative_director.infrastructure.adapters.psychology_input_adapter import (
    PsychologyInputAdapter as CDPsyIn,
)
from creative_director.infrastructure.adapters.ux_input_adapter import UXInputAdapter as CDUXIn
from creative_director.infrastructure.adapters.wireframe_input_adapter import (
    WireframeInputAdapter as CDWireframeIn,
)
from creative_director.infrastructure.container import build_in_memory_environment as build_cd

# --- Phase 14: Design Language ---------------------------------------------- #
from design_language.application.commands import BuildDesignLanguage
from design_language.application.request import DesignLanguageRequest
from design_language.domain.context.context import DesignBrief, ProjectContext as DLProject
from design_language.domain.shared.ids import DesignLanguageSpecId
from design_language.domain.shared.value_objects import IndustryPreset
from design_language.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as DLBrandIn
from design_language.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as DLStrategyIn,
)
from design_language.infrastructure.adapters.creative_director_input_adapter import (
    CreativeDirectorInputAdapter as DLCDIn,
)
from design_language.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter as DLKnowIn,
)
from design_language.infrastructure.adapters.psychology_input_adapter import (
    PsychologyInputAdapter as DLPsyIn,
)
from design_language.infrastructure.container import build_in_memory_environment as build_dl

# --- Phase 15: Component Intelligence --------------------------------------- #
from component_intelligence.application.commands import BuildComposition
from component_intelligence.application.request import ComponentIntelligenceRequest
from component_intelligence.domain.context.context import (
    CompositionBrief,
    ProjectContext as CIProject,
)
from component_intelligence.domain.shared.ids import ComponentSpecId
from component_intelligence.infrastructure.adapters.brand_input_adapter import (
    BrandInputAdapter as CIBrandIn,
)
from component_intelligence.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as CIStrategyIn,
)
from component_intelligence.infrastructure.adapters.creative_director_input_adapter import (
    CreativeDirectorInputAdapter as CICDIn,
)
from component_intelligence.infrastructure.adapters.design_language_input_adapter import (
    DesignLanguageInputAdapter as CIDLIn,
)
from component_intelligence.infrastructure.adapters.ia_input_adapter import IAInputAdapter as CIIAIn
from component_intelligence.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter as CIKnowIn,
)
from component_intelligence.infrastructure.adapters.psychology_input_adapter import (
    PsychologyInputAdapter as CIPsyIn,
)
from component_intelligence.infrastructure.adapters.ux_input_adapter import UXInputAdapter as CIUXIn
from component_intelligence.infrastructure.adapters.wireframe_input_adapter import (
    WireframeInputAdapter as CIWireframeIn,
)
from component_intelligence.infrastructure.container import build_in_memory_environment as build_ci

# --- Phase 16: Design System ------------------------------------------------ #
from design_system.application.commands import BuildDesignSystem
from design_system.application.request import DesignSystemRequest
from design_system.domain.context.context import DesignSystemBrief, ProjectContext as DSProject
from design_system.domain.shared.ids import DesignSystemSpecId
from design_system.infrastructure.adapters.brand_input_adapter import BrandInputAdapter as DSBrandIn
from design_system.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as DSStrategyIn,
)
from design_system.infrastructure.adapters.component_intelligence_input_adapter import (
    ComponentIntelligenceInputAdapter as DSCIIn,
)
from design_system.infrastructure.adapters.creative_director_input_adapter import (
    CreativeDirectorInputAdapter as DSCDIn,
)
from design_system.infrastructure.adapters.design_language_input_adapter import (
    DesignLanguageInputAdapter as DSDLIn,
)
from design_system.infrastructure.adapters.ia_input_adapter import IAInputAdapter as DSIAIn
from design_system.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter as DSKnowIn,
)
from design_system.infrastructure.adapters.psychology_input_adapter import (
    PsychologyInputAdapter as DSPsyIn,
)
from design_system.infrastructure.adapters.ux_input_adapter import UXInputAdapter as DSUXIn
from design_system.infrastructure.adapters.wireframe_input_adapter import (
    WireframeInputAdapter as DSWireframeIn,
)
from design_system.infrastructure.container import build_in_memory_environment as build_ds

# --- Phase 17: Design Orchestrator ------------------------------------------ #
from design_orchestrator.application.commands import BuildExecutionPlan
from design_orchestrator.application.request import OrchestrationRequest
from design_orchestrator.domain.context.context import (
    OrchestrationBrief,
    ProjectContext as DOProject,
    SourceRefs as DOSourceRefs,
)
from design_orchestrator.domain.shared.ids import DesignExecutionPlanId
from design_orchestrator.infrastructure.adapters.brand_input_adapter import (
    BrandInputAdapter as DOBrandIn,
)
from design_orchestrator.infrastructure.adapters.business_strategy_input_adapter import (
    BusinessStrategyInputAdapter as DOStrategyIn,
)
from design_orchestrator.infrastructure.adapters.component_intelligence_input_adapter import (
    ComponentIntelligenceInputAdapter as DOCIIn,
)
from design_orchestrator.infrastructure.adapters.creative_director_input_adapter import (
    CreativeDirectorInputAdapter as DOCDIn,
)
from design_orchestrator.infrastructure.adapters.design_language_input_adapter import (
    DesignLanguageInputAdapter as DODLIn,
)
from design_orchestrator.infrastructure.adapters.design_system_input_adapter import (
    DesignSystemInputAdapter as DODSIn,
)
from design_orchestrator.infrastructure.adapters.ia_input_adapter import IAInputAdapter as DOIAIn
from design_orchestrator.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter as DOKnowIn,
)
from design_orchestrator.infrastructure.adapters.psychology_input_adapter import (
    PsychologyInputAdapter as DOPsyIn,
)
from design_orchestrator.infrastructure.adapters.ux_input_adapter import UXInputAdapter as DOUXIn
from design_orchestrator.infrastructure.adapters.wireframe_input_adapter import (
    WireframeInputAdapter as DOWireframeIn,
)
from design_orchestrator.infrastructure.container import build_in_memory_environment as build_do

# --- Phase 18: Figma Design ------------------------------------------------- #
from figma_design.application.commands import BuildFigmaDesign
from figma_design.application.request import FigmaDesignRequest
from figma_design.domain.context.context import (
    FigmaBrief,
    ProjectContext as FigProject,
    SourceRefs as FigSourceRefs,
)
from figma_design.domain.shared.ids import FigmaDesignModelId
from figma_design.infrastructure.adapters.component_intelligence_input_adapter import (
    ComponentIntelligenceInputAdapter as FigCIIn,
)
from figma_design.infrastructure.adapters.creative_director_input_adapter import (
    CreativeDirectorInputAdapter as FigCDIn,
)
from figma_design.infrastructure.adapters.design_language_input_adapter import (
    DesignLanguageInputAdapter as FigDLIn,
)
from figma_design.infrastructure.adapters.design_orchestrator_input_adapter import (
    DesignOrchestratorInputAdapter as FigDOIn,
)
from figma_design.infrastructure.adapters.design_system_input_adapter import (
    DesignSystemInputAdapter as FigDSIn,
)
from figma_design.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter as FigKnowIn,
)
from figma_design.infrastructure.container import build_in_memory_environment as build_figma

__all__ = ["EngineAgentExecutor"]


_SECTION_BY_KEY = {s.key: s for s in HOMEPAGE_SECTIONS}
_SECTION_ORDER = {s.key: i for i, s in enumerate(HOMEPAGE_SECTIONS, start=1)}


def _ok(summary: str, **artifact: object) -> AgentExecutionResult:
    return AgentExecutionResult(status=ExecutionStatus.OK, summary=summary, artifact=artifact)


def _is_grounded(component: str, *views: object) -> bool:
    """Whether any engine view models the section's component."""
    for view in views:
        for item in getattr(view, "components", []) or []:
            if isinstance(item, dict) and item.get("component") == component:
                return True
        for page in getattr(view, "pages", []) or []:
            for section in page.get("sections", []) or []:
                if section.get("component") == component:
                    return True
    return False


def _industry_preset(industry: str) -> IndustryPreset:
    """Map a free-text industry to the closest Design-Language industry preset."""
    key = industry.strip().upper().replace(" ", "_").replace("-", "_")
    for member in IndustryPreset:
        if member.name == key or member.value.upper() == key:
            return member
    text = industry.lower()
    for member in IndustryPreset:
        if member.value.lower() in text or text in member.value.lower():
            return member
    return next(iter(IndustryPreset))


class EngineAgentExecutor(AgentExecutorPort):
    """Runs each homepage step by invoking the real engine behind it."""

    def __init__(self, knowledge_query: Any) -> None:
        self._knowledge = knowledge_query
        self._contexts: dict[RunId, RunContext] = {}

    # ================================================================== #
    # Port entry point
    # ================================================================== #
    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        context = self._context_for(request)
        try:
            if wf.is_generate_step(request.step_key):
                return await self._run_generate_section(
                    context, wf.section_of_step(request.step_key), request
                )
            if wf.is_approve_step(request.step_key):
                return await self._run_approve_section(
                    context, wf.section_of_step(request.step_key), request
                )
            handler = self._HANDLERS.get(request.step_key)
            if handler is None:
                return AgentExecutionResult(
                    status=ExecutionStatus.FAILED,
                    error=f"No engine handler for step {request.step_key!r}.",
                )
            return await handler(self, context, request)
        except Exception as exc:  # expected engine failures → retryable FAILED (not a raise)
            return AgentExecutionResult(
                status=ExecutionStatus.FAILED,
                summary=f"{request.step_key} failed: {exc}",
                error=str(exc),
            )

    def _context_for(self, request: AgentExecutionRequest) -> RunContext:
        context = self._contexts.get(request.run_id)
        if context is None:
            brief = HomepageBrief.from_mapping(request.brief, str(request.run_id))
            context = RunContext(brief=brief, knowledge_query=self._knowledge)
            context.request = HomepageRequest.from_brief(request.brief)
            self._contexts[request.run_id] = context
        return context

    # ================================================================== #
    # Step handlers — one real engine each
    # ================================================================== #
    async def _run_research(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = build_research()
        view = await env.facade.research(
            Research(request=ResearchRequest.build(ctx.brief.project_id, ctx.brief.goal))
        )
        ctx.set_output("research", env.facade, ResearchReportId.from_string(view.report_id))
        return _ok(
            f"Research complete for {ctx.brief.product_category}.",
            research_report_id=view.report_id,
        )

    async def _run_competitor(self, ctx: RunContext, _req: AgentExecutionRequest):
        Dim = CompetitorDimension
        c1, c2, c3 = CompetitorId.new(), CompetitorId.new(), CompetitorId.new()
        competitors = (
            Competitor(id=c1, name="Aesop", industry=ctx.brief.industry, market="premium"),
            Competitor(id=c2, name="Glossier", industry=ctx.brief.industry, market="premium"),
            Competitor(id=c3, name="Sephora", industry=ctx.brief.industry, market="mass"),
        )

        def obs(cid, dim, finding, strength):
            return Observation(
                id=ObservationId.new(), competitor_id=cid, dimension=dim, finding=finding,
                source=ObservationSource.MANUAL, confidence=CompConfidence.of(0.9),
                strength=CompScore.of(strength),
            )

        observations = ObservationSet.of([
            obs(c1, Dim.CONVERSION_PATTERNS, "Prominent single CTA", 90),
            obs(c2, Dim.CONVERSION_PATTERNS, "Sticky add-to-cart", 82),
            obs(c3, Dim.CONVERSION_PATTERNS, "One-click checkout", 92),
            obs(c1, Dim.TYPOGRAPHY, "Editorial serif", 88),
            obs(c2, Dim.TYPOGRAPHY, "Clean sans-serif", 78),
            obs(c1, Dim.TRUST_STRATEGY, "Visible reviews", 80),
            obs(c2, Dim.TRUST_STRATEGY, "User-generated content", 75),
        ])
        advisor = InMemoryKnowledgeAdvisor({
            Dim.CONVERSION_PATTERNS: [
                AdvisedPrinciple("kc", "kc-v1", "conversion_optimization", "cro bp",
                                 "One high-contrast CTA lifts conversion.", "NNG", 0.85, "rel")
            ],
            Dim.TYPOGRAPHY: [
                AdvisedPrinciple("kt", "kt-v1", "typography", "type bp",
                                 "High-contrast serif conveys editorial trust.", "NNG", 0.85, "rel")
            ],
        })
        env = build_competitive(
            data_source=InMemoryDataSource(observations), advisor=advisor
        )
        brief = CompetitiveBrief.build(
            ctx.brief.industry, market=ctx.brief.market,
            business_goals=list(ctx.brief.business_goals), client_name=ctx.brief.brand_name,
            competitors=list(competitors),
        )
        view = await env.facade.analyze(AnalyzeCompetitors(brief=brief))
        ctx.set_output("competitive", env.facade, ReportId.from_string(view.report_id))
        return _ok("Competitor analysis complete.", competitive_report_id=view.report_id)

    async def _run_business_strategy(self, ctx: RunContext, _req: AgentExecutionRequest):
        research_in = StResearchIn(ctx.facade("research"), ctx.ref("research"))
        env = build_strategy(research=research_in)
        view = await env.facade.build(BuildStrategy(request=StrategyRequest(
            brand=StBrand(
                name=ctx.brief.brand_name, industry=ctx.brief.industry, maturity="established",
                descriptors=ctx.brief.descriptors,
            ),
            project=StProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
            goals=StGoal(
                business_goals=ctx.brief.business_goals, user_goals=ctx.brief.user_goals
            ),
        )))
        ctx.set_output("strategy", env.facade, StrategyReportId.from_string(view.report_id))
        return _ok("Business strategy set.", strategy_report_id=view.report_id)

    async def _run_brand_strategy(self, ctx: RunContext, _req: AgentExecutionRequest):
        strategy_in = BrStrategyIn(ctx.facade("strategy"), ctx.ref("strategy"))
        env = build_brand(business_strategy=strategy_in)
        view = await env.facade.build(BuildBrand(request=BrandRequest(
            brief=BrandBrief(
                name=ctx.brief.brand_name, industry=ctx.brief.industry, maturity="established",
                descriptors=ctx.brief.descriptors,
            ),
            project=BrProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output("brand", env.facade, BrandReportId.from_string(view.report_id))
        return _ok("Brand strategy set.", brand_report_id=view.report_id)

    async def _run_psychology(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = build_psychology(
            brand=PsyBrandIn(ctx.facade("brand"), ctx.ref("brand")),
            business_strategy=PsyStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
        )
        view = await env.facade.build(BuildPsychology(request=PsychologyRequest(
            brief=PsychologyBrief(
                product_category=ctx.brief.product_category, price_band=ctx.brief.market,
                purchase_risk="high",
            ),
            project=PsyProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output("psychology", env.facade, PsychologyReportId.from_string(view.report_id))
        return _ok("Customer psychology profiled.", psychology_report_id=view.report_id)

    async def _run_ux(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = build_ux(
            psychology=UXPsyIn(ctx.facade("psychology"), ctx.ref("psychology")),
            brand=UXBrandIn(ctx.facade("brand"), ctx.ref("brand")),
            business_strategy=UXStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
            knowledge=UXKnowIn(ctx.knowledge_query),
        )
        view = await env.facade.build(BuildUXStrategy(request=UXRequest(
            brief=UXBrief(product_category=ctx.brief.product_category),
            project=UXProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output("ux", env.facade, UXReportId.from_string(view.report_id))
        return _ok("UX strategy defined.", ux_report_id=view.report_id)

    async def _run_ia(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = build_ia(
            ux=IAUXIn(ctx.facade("ux"), ctx.ref("ux")),
            psychology=IAPsyIn(ctx.facade("psychology"), ctx.ref("psychology")),
            brand=IABrandIn(ctx.facade("brand"), ctx.ref("brand")),
            business_strategy=IAStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
            knowledge=IAKnowIn(ctx.knowledge_query),
        )
        view = await env.facade.build(BuildIA(request=IARequest(
            brief=IABrief(product_category=ctx.brief.product_category, catalog_scale="large"),
            project=IAProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output("ia", env.facade, IAReportId.from_string(view.report_id))
        return _ok("Information architecture defined.", ia_report_id=view.report_id)

    async def _run_wireframe(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = build_wireframe(
            ia=WFIAIn(ctx.facade("ia"), ctx.ref("ia")),
            ux=WFUXIn(ctx.facade("ux"), ctx.ref("ux")),
            psychology=WFPsyIn(ctx.facade("psychology"), ctx.ref("psychology")),
            business_strategy=WFStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
            knowledge=WFKnowIn(ctx.knowledge_query),
        )
        view = await env.facade.plan(BuildWireframePlan(request=WireframeRequest(
            brief=WireframeBrief(product_category=ctx.brief.product_category, catalog_scale="large"),
            project=WFProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output("wireframe", env.facade, WireframePlanId.from_string(view.plan_id))
        return _ok("Wireframe plan complete.", wireframe_plan_id=view.plan_id)

    def _build_cd_env(self, ctx: RunContext):
        return build_cd(
            wireframe=CDWireframeIn(ctx.facade("wireframe"), ctx.ref("wireframe")),
            ia=CDIAIn(ctx.facade("ia"), ctx.ref("ia")),
            ux=CDUXIn(ctx.facade("ux"), ctx.ref("ux")),
            business_strategy=CDStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
            psychology=CDPsyIn(ctx.facade("psychology"), ctx.ref("psychology")),
            knowledge=CDKnowIn(ctx.knowledge_query),
        )

    async def _run_cd_review(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = self._build_cd_env(ctx)
        subject = ReviewSubject(
            kind=SubjectKind.WIREFRAME_PLAN, reference=ctx.ref_str("wireframe"),
            label="Homepage wireframe plan",
        )
        view = await env.facade.review(BuildReview(request=ReviewRequest(
            subject=subject,
            policy=ReviewPolicy(profile=cd_profile_for(ReviewProfileKind.D2C), mode=CDMode.AUTOMATIC),
            project=CDProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output(
            "creative_director", env.facade, CreativeDirectorReviewId.from_string(view.review_id)
        )
        if view.is_approved:
            return _ok(
                f"Creative Director approved the wireframe (score {view.quality.overall_score:.0f}).",
                review_id=view.review_id, overall_score=view.quality.overall_score,
            )
        notes = _improvement_notes(view.improvement_matrix)
        return AgentExecutionResult(
            status=ExecutionStatus.REJECTED,
            summary=f"Creative Director requested changes to the wireframe "
            f"(score {view.quality.overall_score:.0f}).",
            revision_notes=notes,
            artifact={"review_id": view.review_id},
        )

    async def _run_design_language(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = build_dl(
            brand=DLBrandIn(ctx.facade("brand"), ctx.ref("brand")),
            business_strategy=DLStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
            psychology=DLPsyIn(ctx.facade("psychology"), ctx.ref("psychology")),
            creative_director=DLCDIn(ctx.facade("creative_director"), ctx.ref("creative_director")),
            knowledge=DLKnowIn(ctx.knowledge_query),
        )
        view = await env.facade.design(BuildDesignLanguage(request=DesignLanguageRequest(
            brief=DesignBrief(
                industry=_industry_preset(ctx.brief.industry), tier=ctx.brief.market,
                product_category=ctx.brief.product_category,
            ),
            project=DLProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output("design_language", env.facade, DesignLanguageSpecId.from_string(view.spec_id))
        return _ok("Design language selected.", design_language_spec_id=view.spec_id)

    async def _run_component_intelligence(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = build_ci(
            wireframe=CIWireframeIn(ctx.facade("wireframe"), ctx.ref("wireframe")),
            ia=CIIAIn(ctx.facade("ia"), ctx.ref("ia")),
            ux=CIUXIn(ctx.facade("ux"), ctx.ref("ux")),
            business_strategy=CIStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
            brand=CIBrandIn(ctx.facade("brand"), ctx.ref("brand")),
            psychology=CIPsyIn(ctx.facade("psychology"), ctx.ref("psychology")),
            creative_director=CICDIn(ctx.facade("creative_director"), ctx.ref("creative_director")),
            design_language=CIDLIn(ctx.facade("design_language"), ctx.ref("design_language")),
            knowledge=CIKnowIn(ctx.knowledge_query),
        )
        view = await env.facade.compose(BuildComposition(request=ComponentIntelligenceRequest(
            brief=CompositionBrief(product_category=ctx.brief.product_category, catalog_scale="large"),
            project=CIProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output("component_intelligence", env.facade, ComponentSpecId.from_string(view.spec_id))
        return _ok("Component intelligence composed.", component_spec_id=view.spec_id)

    async def _run_design_system(self, ctx: RunContext, _req: AgentExecutionRequest):
        env = build_ds(
            design_language=DSDLIn(ctx.facade("design_language"), ctx.ref("design_language")),
            component_intelligence=DSCIIn(
                ctx.facade("component_intelligence"), ctx.ref("component_intelligence")
            ),
            creative_director=DSCDIn(ctx.facade("creative_director"), ctx.ref("creative_director")),
            business_strategy=DSStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
            brand=DSBrandIn(ctx.facade("brand"), ctx.ref("brand")),
            psychology=DSPsyIn(ctx.facade("psychology"), ctx.ref("psychology")),
            ux=DSUXIn(ctx.facade("ux"), ctx.ref("ux")),
            ia=DSIAIn(ctx.facade("ia"), ctx.ref("ia")),
            wireframe=DSWireframeIn(ctx.facade("wireframe"), ctx.ref("wireframe")),
            knowledge=DSKnowIn(ctx.knowledge_query),
        )
        view = await env.facade.build(BuildDesignSystem(request=DesignSystemRequest(
            brief=DesignSystemBrief(product_category=ctx.brief.product_category),
            project=DSProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform,
                market=ctx.brief.market,
            ),
        )))
        ctx.set_output("design_system", env.facade, DesignSystemSpecId.from_string(view.spec_id))
        return _ok("Design system mapped.", design_system_spec_id=view.spec_id)

    async def _run_validate_inputs(self, ctx: RunContext, req: AgentExecutionRequest):
        request = ctx.request or HomepageRequest.from_brief(req.brief)
        ctx.request = request
        validation = request.validate()
        if not validation.is_valid:
            return AgentExecutionResult(
                status=ExecutionStatus.NEEDS_INPUT,
                summary="Missing required inputs: " + ", ".join(validation.missing) + ".",
                artifact={"missing": list(validation.missing), "warnings": list(validation.warnings)},
            )
        return _ok(
            f"Inputs validated for {request.brand_name}.",
            warnings=list(validation.warnings),
            validation=validation.to_json(),
        )

    async def _run_generate_homepage_plan(self, ctx: RunContext, _req: AgentExecutionRequest):
        """Run the Design Orchestrator (P17) to produce the machine-ready homepage backbone."""
        do_env = build_do(
            design_system=DODSIn(ctx.facade("design_system"), ctx.ref("design_system")),
            component_intelligence=DOCIIn(
                ctx.facade("component_intelligence"), ctx.ref("component_intelligence")
            ),
            wireframe=DOWireframeIn(ctx.facade("wireframe"), ctx.ref("wireframe")),
            creative_director=DOCDIn(ctx.facade("creative_director"), ctx.ref("creative_director")),
            design_language=DODLIn(ctx.facade("design_language"), ctx.ref("design_language")),
            ia=DOIAIn(ctx.facade("ia"), ctx.ref("ia")),
            ux=DOUXIn(ctx.facade("ux"), ctx.ref("ux")),
            psychology=DOPsyIn(ctx.facade("psychology"), ctx.ref("psychology")),
            brand=DOBrandIn(ctx.facade("brand"), ctx.ref("brand")),
            business_strategy=DOStrategyIn(ctx.facade("strategy"), ctx.ref("strategy")),
            knowledge=DOKnowIn(ctx.knowledge_query),
        )
        do_view = await do_env.facade.orchestrate(BuildExecutionPlan(request=OrchestrationRequest(
            brief=OrchestrationBrief(product_category=ctx.brief.product_category),
            project=DOProject(
                project_id=ctx.brief.project_id, platform=ctx.brief.platform, market=ctx.brief.market
            ),
            source_refs=DOSourceRefs(
                design_system_spec_id=ctx.ref_str("design_system"),
                component_spec_id=ctx.ref_str("component_intelligence"),
                wireframe_plan_id=ctx.ref_str("wireframe"),
            ),
        )))
        ctx.set_output(
            "orchestrator", do_env.facade, DesignExecutionPlanId.from_string(do_view.plan_id)
        )
        return _ok(
            "Homepage plan backbone generated; ready to design sections one at a time.",
            execution_plan_id=do_view.plan_id,
        )

    # ------------------------------------------------------------------ #
    # Per-section generation & approval                                   #
    # ------------------------------------------------------------------ #
    async def _run_generate_section(
        self, ctx: RunContext, section_key: str, req: AgentExecutionRequest
    ) -> AgentExecutionResult:
        spec = _SECTION_BY_KEY[section_key]
        ds_view = await ctx.facade("design_system").get(ctx.ref("design_system"))
        ci_view = await ctx.facade("component_intelligence").get(ctx.ref("component_intelligence"))
        do_view = await ctx.facade("orchestrator").get(ctx.ref("orchestrator"))
        grounded = _is_grounded(spec.component, ds_view, ci_view, do_view)
        assert ctx.request is not None
        plan = project_section(
            spec,
            ctx.request,
            order=_SECTION_ORDER[section_key],
            design_system_view=ds_view,
            component_intelligence_view=ci_view,
            orchestrator_view=do_view,
            evidence_refs=(
                ctx.ref_str("design_system"),
                ctx.ref_str("component_intelligence"),
                ctx.ref_str("orchestrator"),
            ),
            attempt=req.attempt,
            notes=req.revision_notes,
        )
        ctx.set_section_plan(plan)
        return _ok(
            f"Generated the {spec.title} plan (attempt {req.attempt}).",
            section=section_key,
            grounded=grounded,
            plan=plan.to_json(),
        )

    async def _run_approve_section(
        self, ctx: RunContext, section_key: str, req: AgentExecutionRequest
    ) -> AgentExecutionResult:
        plan = ctx.section_plan(section_key)
        if plan is None:
            return AgentExecutionResult(
                status=ExecutionStatus.FAILED,
                error=f"Section {section_key!r} was not generated before approval.",
            )
        generated = req.artifacts.get(wf.generate_step_key(section_key))
        grounded = bool(generated.get("grounded", True)) if isinstance(generated, Mapping) else True
        score, findings = score_section(plan, grounded=grounded)
        if meets_bar(score):
            ctx.set_section_plan(plan.with_review(score, ApprovalStatus.APPROVED))
            return _ok(
                f"Approved the {plan.title} (score {score:.0f}/100).",
                section=section_key, review_score=score, approval_status="approved",
            )
        ctx.set_section_plan(plan.with_review(score, ApprovalStatus.IMPROVING))
        return AgentExecutionResult(
            status=ExecutionStatus.REJECTED,
            summary=f"{plan.title} scored {score:.0f}/100 (< 95); improving only this section.",
            revision_notes=findings,
            artifact={"section": section_key, "review_score": score},
        )

    # ------------------------------------------------------------------ #
    # Finalisation & sign-off                                             #
    # ------------------------------------------------------------------ #
    async def _run_finalize(self, ctx: RunContext, _req: AgentExecutionRequest):
        sections = ctx.approved_section_plans or ctx.section_plans()
        brand = ctx.request.brand_name if ctx.request else ctx.brief.brand_name
        plan = HomepageDesignPlan(
            brand_name=brand or "Storefront",
            project_id=ctx.brief.project_id,
            sections=sections,
            source_refs={
                "design_system": ctx.ref_str("design_system"),
                "component_intelligence": ctx.ref_str("component_intelligence"),
                "orchestrator": ctx.ref_str("orchestrator"),
            },
        )
        ctx.homepage_plan = plan
        return _ok(
            f"Homepage plan finalised: {len(plan)} sections, overall {plan.overall_score:.0f}/100, "
            f"ready_for_figma={plan.ready_for_figma}.",
            section_count=len(plan),
            overall_score=plan.overall_score,
            ready_for_figma=plan.ready_for_figma,
        )

    async def _run_final_approval(self, ctx: RunContext, _req: AgentExecutionRequest):
        plan = ctx.homepage_plan
        if plan is None:
            return _ok("Awaiting a finalised homepage plan.")
        # A manual gate: present the finished plan and pause for the human sign-off.
        return _ok(
            f"Homepage design plan ready for approval: {len(plan)} sections, overall "
            f"{plan.overall_score:.0f}/100, ready for Figma generation.",
            section_count=len(plan),
            overall_score=plan.overall_score,
            ready_for_figma=plan.ready_for_figma,
        )

    # ================================================================== #
    # Dispatch table (fixed steps; section steps are dispatched by prefix)
    # ================================================================== #
    _HANDLERS = {
        wf.STEP_VALIDATE_INPUTS: _run_validate_inputs,
        wf.STEP_RESEARCH: _run_research,
        wf.STEP_COMPETITOR_ANALYSIS: _run_competitor,
        wf.STEP_BUSINESS_STRATEGY: _run_business_strategy,
        wf.STEP_BRAND_STRATEGY: _run_brand_strategy,
        wf.STEP_CUSTOMER_PSYCHOLOGY: _run_psychology,
        wf.STEP_UX_STRATEGY: _run_ux,
        wf.STEP_INFORMATION_ARCHITECTURE: _run_ia,
        wf.STEP_WIREFRAME_PLANNING: _run_wireframe,
        wf.STEP_CD_REVIEW: _run_cd_review,
        wf.STEP_DESIGN_LANGUAGE: _run_design_language,
        wf.STEP_COMPONENT_INTELLIGENCE: _run_component_intelligence,
        wf.STEP_DESIGN_SYSTEM_MAPPING: _run_design_system,
        wf.STEP_GENERATE_HOMEPAGE_PLAN: _run_generate_homepage_plan,
        wf.STEP_FINALIZE: _run_finalize,
        wf.STEP_FINAL_APPROVAL: _run_final_approval,
    }


def _improvement_notes(improvement_matrix: list[dict]) -> tuple[str, ...]:
    """Extract concrete revision notes from the Creative Director's improvement matrix."""
    notes: list[str] = []
    for item in improvement_matrix:
        if not isinstance(item, Mapping):
            notes.append(str(item))
            continue
        text = (
            item.get("action")
            or item.get("recommendation")
            or item.get("finding")
            or item.get("summary")
            or item.get("category")
        )
        if text:
            notes.append(str(text))
    return tuple(dict.fromkeys(notes))
