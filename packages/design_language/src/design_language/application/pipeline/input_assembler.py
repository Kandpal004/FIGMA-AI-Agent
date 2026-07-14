"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (business strategy, brand, psychology, the
Creative Director, knowledge, research, competitor) and folds them, with the brief and project,
into a single :class:`LanguageInput`. Ports are queried concurrently; any that returns nothing
simply contributes nothing. Brand is the primary driver of the DNA; the Creative Director sets
the approved quality direction; psychology shapes emotional posture; knowledge grounds
restraint and timelessness.
"""

from __future__ import annotations

import asyncio

from design_language.application.contracts import LanguageInput, RawSignal
from design_language.application.ports.brand_input import BrandInputPort
from design_language.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_language.application.ports.competitor_insight import CompetitorInsightPort
from design_language.application.ports.creative_director_input import CreativeDirectorInputPort
from design_language.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_language.application.ports.psychology_input import PsychologyInputPort
from design_language.application.ports.research_input import ResearchInputPort
from design_language.application.request import DesignLanguageRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the language input from the seven signal ports."""

    # The visual-language topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "premium visual systems",
        "typographic scale",
        "spacing rhythm",
        "grid systems",
        "colour restraint",
        "elevation and depth",
        "motion restraint",
        "visual timelessness",
        "design consistency",
        "industry visual conventions",
    )

    async def assemble(
        self,
        request: DesignLanguageRequest,
        *,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        creative_director: CreativeDirectorInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
    ) -> LanguageInput:
        results = await asyncio.gather(
            business_strategy.gather(request.project),
            brand.gather(request.project),
            psychology.gather(request.project),
            creative_director.gather(request.project),
            knowledge.advise(self._TOPICS, request.project),
            research.gather(request.project),
            competitor.gather(request.project),
        )
        signals: list[RawSignal] = [s for group in results for s in group]
        return LanguageInput(
            brief=request.brief, project=request.project, signals=tuple(signals)
        )
