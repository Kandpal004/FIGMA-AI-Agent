"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (Information Architecture, UX, business
strategy, brand, psychology, knowledge, research, competitor, reasoning) and folds them, with
the request's context, into a single :class:`WireframeInput`. Ports are queried concurrently;
any that returns nothing simply contributes nothing. The IA is the primary driver — the
wireframe executes the information architecture; psychology shapes trust placement; knowledge
grounds structure in planning best-practice.
"""

from __future__ import annotations

import asyncio

from wireframe.application.contracts import RawSignal, WireframeInput
from wireframe.application.ports.brand_input import BrandInputPort
from wireframe.application.ports.business_strategy_input import BusinessStrategyInputPort
from wireframe.application.ports.competitor_insight import CompetitorInsightPort
from wireframe.application.ports.ia_input import IAInputPort
from wireframe.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from wireframe.application.ports.psychology_input import PsychologyInputPort
from wireframe.application.ports.reasoning import ReasoningPort
from wireframe.application.ports.research_input import ResearchInputPort
from wireframe.application.ports.ux_input import UXInputPort
from wireframe.application.request import WireframeRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the wireframe input from the nine signal ports."""

    # The planning topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "wireframe planning",
        "page section order",
        "component composition",
        "content hierarchy",
        "conversion section placement",
        "trust signals placement",
        "product page structure",
        "checkout flow structure",
        "accessibility requirements",
        "web performance budget",
        "design approval workflow",
    )

    async def assemble(
        self,
        request: WireframeRequest,
        *,
        ia: IAInputPort,
        ux: UXInputPort,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
    ) -> WireframeInput:
        results = await asyncio.gather(
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
        return WireframeInput(
            brief=request.brief, project=request.project, signals=tuple(signals)
        )
