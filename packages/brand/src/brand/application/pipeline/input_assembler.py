"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (business strategy, knowledge, research,
competitor, reasoning) and folds them, with the request's context, into a single
:class:`BrandInput`. Ports are queried concurrently; any that returns nothing simply
contributes nothing. Business strategy is the primary driver; the rest sharpen it.
"""

from __future__ import annotations

import asyncio

from brand.application.contracts import BrandInput, RawSignal
from brand.application.ports.business_strategy_input import BusinessStrategyInputPort
from brand.application.ports.competitor_insight import CompetitorInsightPort
from brand.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from brand.application.ports.reasoning import ReasoningPort
from brand.application.ports.research_input import ResearchInputPort
from brand.application.request import BrandRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the brand input from the five signal ports."""

    # The brand topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "brand positioning",
        "brand personality",
        "brand voice and tone",
        "visual identity",
        "typography",
        "color",
        "trust and credibility",
        "brand consistency",
    )

    async def assemble(
        self,
        request: BrandRequest,
        *,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
    ) -> BrandInput:
        strategy_i, knowledge_i, research_i, competitor_i, reasoning_i = (
            await asyncio.gather(
                business_strategy.gather(request.project),
                knowledge.advise(self._TOPICS, request.project),
                research.gather(request.project),
                competitor.gather(request.project),
                reasoning.gather(request.project),
            )
        )
        signals: list[RawSignal] = [
            *strategy_i,
            *knowledge_i,
            *research_i,
            *competitor_i,
            *reasoning_i,
        ]
        return BrandInput(
            brief=request.brief, project=request.project, signals=tuple(signals)
        )
