"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (brand, business strategy, knowledge,
research, competitor, reasoning) and folds them, with the request's context, into a
single :class:`PsychologyInput`. Ports are queried concurrently; any that returns nothing
simply contributes nothing. Brand and business strategy are the primary drivers; the rest
sharpen the model.
"""

from __future__ import annotations

import asyncio

from psychology.application.contracts import PsychologyInput, RawSignal
from psychology.application.ports.brand_input import BrandInputPort
from psychology.application.ports.business_strategy_input import (
    BusinessStrategyInputPort,
)
from psychology.application.ports.competitor_insight import CompetitorInsightPort
from psychology.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from psychology.application.ports.reasoning import ReasoningPort
from psychology.application.ports.research_input import ResearchInputPort
from psychology.application.request import PsychologyRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the psychology input from the six signal ports."""

    # The behavioral topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "customer awareness",
        "purchase motivation",
        "purchase anxiety",
        "buyer trust",
        "loss aversion",
        "social proof",
        "scarcity and urgency",
        "decision friction",
        "retention psychology",
    )

    async def assemble(
        self,
        request: PsychologyRequest,
        *,
        brand: BrandInputPort,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
    ) -> PsychologyInput:
        brand_i, strategy_i, knowledge_i, research_i, competitor_i, reasoning_i = (
            await asyncio.gather(
                brand.gather(request.project),
                business_strategy.gather(request.project),
                knowledge.advise(self._TOPICS, request.project),
                research.gather(request.project),
                competitor.gather(request.project),
                reasoning.gather(request.project),
            )
        )
        signals: list[RawSignal] = [
            *brand_i,
            *strategy_i,
            *knowledge_i,
            *research_i,
            *competitor_i,
            *reasoning_i,
        ]
        return PsychologyInput(
            brief=request.brief, project=request.project, signals=tuple(signals)
        )
