"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (psychology, brand, business strategy,
knowledge, research, competitor, reasoning) and folds them, with the request's context,
into a single :class:`UXInput`. Ports are queried concurrently; any that returns nothing
simply contributes nothing. Psychology is the primary driver; brand and business strategy
shape it; knowledge grounds it in UX law.
"""

from __future__ import annotations

import asyncio

from ux.application.contracts import RawSignal, UXInput
from ux.application.ports.brand_input import BrandInputPort
from ux.application.ports.business_strategy_input import BusinessStrategyInputPort
from ux.application.ports.competitor_insight import CompetitorInsightPort
from ux.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from ux.application.ports.psychology_input import PsychologyInputPort
from ux.application.ports.reasoning import ReasoningPort
from ux.application.ports.research_input import ResearchInputPort
from ux.application.request import UXRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the UX input from the seven signal ports."""

    # The UX topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "usability heuristics",
        "navigation patterns",
        "checkout ux",
        "form design",
        "progressive disclosure",
        "cognitive load",
        "accessibility wcag",
        "conversion optimization",
        "trust and credibility",
    )

    async def assemble(
        self,
        request: UXRequest,
        *,
        psychology: PsychologyInputPort,
        brand: BrandInputPort,
        business_strategy: BusinessStrategyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
    ) -> UXInput:
        psych_i, brand_i, strategy_i, knowledge_i, research_i, competitor_i, reasoning_i = (
            await asyncio.gather(
                psychology.gather(request.project),
                brand.gather(request.project),
                business_strategy.gather(request.project),
                knowledge.advise(self._TOPICS, request.project),
                research.gather(request.project),
                competitor.gather(request.project),
                reasoning.gather(request.project),
            )
        )
        signals: list[RawSignal] = [
            *psych_i, *brand_i, *strategy_i, *knowledge_i,
            *research_i, *competitor_i, *reasoning_i,
        ]
        return UXInput(brief=request.brief, project=request.project, signals=tuple(signals))
