"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (the wireframe subject, IA, UX, business
strategy, brand, psychology, knowledge, research, competitor, reasoning) and folds them, with
the review's context, into a single :class:`ReviewInput`. Ports are queried concurrently; any
that returns nothing simply contributes nothing. The wireframe plan is the primary subject;
the rest supply the standards the Creative Director judges it against.
"""

from __future__ import annotations

import asyncio

from creative_director.application.contracts import RawSignal, ReviewInput
from creative_director.application.ports.brand_input import BrandInputPort
from creative_director.application.ports.business_strategy_input import BusinessStrategyInputPort
from creative_director.application.ports.competitor_insight import CompetitorInsightPort
from creative_director.application.ports.ia_input import IAInputPort
from creative_director.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from creative_director.application.ports.psychology_input import PsychologyInputPort
from creative_director.application.ports.reasoning import ReasoningPort
from creative_director.application.ports.research_input import ResearchInputPort
from creative_director.application.ports.ux_input import UXInputPort
from creative_director.application.ports.wireframe_input import WireframeInputPort
from creative_director.application.request import ReviewRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the review input from the ten signal ports."""

    # The review topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "premium ecommerce standards",
        "conversion rate optimization",
        "trust signals ecommerce",
        "typography hierarchy",
        "spacing and layout",
        "web accessibility wcag",
        "web performance",
        "mobile commerce",
        "shopify theme feasibility",
        "magento theme feasibility",
        "design consistency",
    )

    async def assemble(
        self,
        request: ReviewRequest,
        *,
        wireframe: WireframeInputPort,
        ia: IAInputPort,
        ux: UXInputPort,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
    ) -> ReviewInput:
        results = await asyncio.gather(
            wireframe.gather(request.project),
            ia.gather(request.project),
            ux.gather(request.project),
            business_strategy.gather(request.project),
            brand.gather(request.project),
            psychology.gather(request.project),
            knowledge.advise(self._TOPICS, request.project),
            research.gather(request.project),
            competitor.gather(request.project),
            reasoning.gather(request.project),
        )
        signals: list[RawSignal] = [s for group in results for s in group]
        return ReviewInput(
            subject=request.subject, project=request.project, signals=tuple(signals)
        )
