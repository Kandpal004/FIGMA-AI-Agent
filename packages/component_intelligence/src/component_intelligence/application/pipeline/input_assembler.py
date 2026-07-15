"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (business strategy, brand, psychology, UX, IA,
wireframe, Creative Director, Design Language, knowledge, research, competitor) and folds them,
with the brief and project, into a single :class:`ComponentInput`. Ports are queried
concurrently; any that returns nothing simply contributes nothing. The Wireframe plan is the
primary driver of which components exist; the Design Language grounds variants and tokens; the
Creative Director sets the quality bar; psychology and business ground trust and conversion.
"""

from __future__ import annotations

import asyncio

from component_intelligence.application.contracts import ComponentInput, RawSignal
from component_intelligence.application.ports.brand_input import BrandInputPort
from component_intelligence.application.ports.business_strategy_input import BusinessStrategyInputPort
from component_intelligence.application.ports.competitor_insight import CompetitorInsightPort
from component_intelligence.application.ports.creative_director_input import CreativeDirectorInputPort
from component_intelligence.application.ports.design_language_input import DesignLanguageInputPort
from component_intelligence.application.ports.ia_input import IAInputPort
from component_intelligence.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from component_intelligence.application.ports.psychology_input import PsychologyInputPort
from component_intelligence.application.ports.research_input import ResearchInputPort
from component_intelligence.application.ports.ux_input import UXInputPort
from component_intelligence.application.ports.wireframe_input import WireframeInputPort
from component_intelligence.application.request import ComponentIntelligenceRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the component input from the eleven signal ports."""

    # The component-intelligence topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "ecommerce component patterns",
        "conversion rate optimization components",
        "trust components",
        "atomic design",
        "component composition",
        "product page components",
        "navigation components",
        "cart and checkout components",
        "component anti-patterns",
        "mobile commerce components",
    )

    async def assemble(
        self,
        request: ComponentIntelligenceRequest,
        *,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        ux: UXInputPort,
        ia: IAInputPort,
        wireframe: WireframeInputPort,
        creative_director: CreativeDirectorInputPort,
        design_language: DesignLanguageInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
    ) -> ComponentInput:
        results = await asyncio.gather(
            business_strategy.gather(request.project),
            brand.gather(request.project),
            psychology.gather(request.project),
            ux.gather(request.project),
            ia.gather(request.project),
            wireframe.gather(request.project),
            creative_director.gather(request.project),
            design_language.gather(request.project),
            knowledge.advise(self._TOPICS, request.project),
            research.gather(request.project),
            competitor.gather(request.project),
        )
        signals: list[RawSignal] = [s for group in results for s in group]
        return ComponentInput(
            brief=request.brief, project=request.project, signals=tuple(signals)
        )
