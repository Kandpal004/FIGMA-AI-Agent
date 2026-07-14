"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (UX, psychology, brand, business strategy,
knowledge, research, competitor, reasoning) and folds them, with the request's context, into
a single :class:`IAInput`. Ports are queried concurrently; any that returns nothing simply
contributes nothing. UX is the primary driver; psychology shapes placement; knowledge grounds
structure in IA best-practice.
"""

from __future__ import annotations

import asyncio

from ia.application.contracts import IAInput, RawSignal
from ia.application.ports.brand_input import BrandInputPort
from ia.application.ports.business_strategy_input import BusinessStrategyInputPort
from ia.application.ports.competitor_insight import CompetitorInsightPort
from ia.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from ia.application.ports.psychology_input import PsychologyInputPort
from ia.application.ports.reasoning import ReasoningPort
from ia.application.ports.research_input import ResearchInputPort
from ia.application.ports.ux_input import UXInputPort
from ia.application.request import IARequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the IA input from the eight signal ports."""

    # The IA topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "information architecture",
        "ecommerce navigation",
        "faceted navigation",
        "site search",
        "breadcrumbs",
        "internal linking seo",
        "product page structure",
        "collection page structure",
        "cross sell upsell",
    )

    async def assemble(
        self,
        request: IARequest,
        *,
        ux: UXInputPort,
        psychology: PsychologyInputPort,
        brand: BrandInputPort,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
    ) -> IAInput:
        results = await asyncio.gather(
            ux.gather(request.project),
            psychology.gather(request.project),
            brand.gather(request.project),
            business_strategy.gather(request.project),
            knowledge.advise(self._TOPICS, request.project),
            research.gather(request.project),
            competitor.gather(request.project),
            reasoning.gather(request.project),
        )
        signals: list[RawSignal] = [s for group in results for s in group]
        return IAInput(brief=request.brief, project=request.project, signals=tuple(signals))
