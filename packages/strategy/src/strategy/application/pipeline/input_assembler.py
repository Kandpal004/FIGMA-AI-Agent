"""Stage 1 — Input Assembly.

Gathers neutral insights from every input port (research, knowledge, competitor,
reasoning) and folds them, with the request's context, into a single
:class:`StrategyInput`. Ports are queried concurrently; any that returns nothing simply
contributes nothing.
"""

from __future__ import annotations

import asyncio

from strategy.application.contracts import RawInsight, StrategyInput
from strategy.application.ports.competitor_insight import CompetitorInsightPort
from strategy.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from strategy.application.ports.reasoning import ReasoningPort
from strategy.application.ports.research_input import ResearchInputPort
from strategy.application.request import StrategyRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the strategy input from the four evidence ports."""

    # The strategic topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "brand positioning",
        "customer trust",
        "conversion optimization",
        "pricing strategy",
        "messaging",
        "retention",
        "value proposition",
        "social proof",
    )

    async def assemble(
        self,
        request: StrategyRequest,
        *,
        research: ResearchInputPort,
        knowledge: KnowledgeAdvisorPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
    ) -> StrategyInput:
        research_i, knowledge_i, competitor_i, reasoning_i = await asyncio.gather(
            research.gather(request.project),
            knowledge.advise(self._TOPICS, request.project),
            competitor.gather(request.project),
            reasoning.gather(request.project),
        )
        insights: list[RawInsight] = [
            *research_i,
            *knowledge_i,
            *competitor_i,
            *reasoning_i,
        ]
        return StrategyInput(
            brand=request.brand,
            project=request.project,
            goals=request.goals,
            insights=tuple(insights),
        )
