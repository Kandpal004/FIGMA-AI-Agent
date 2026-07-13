"""Competitive reasoner — which competitors should be researched."""

from __future__ import annotations

from reasoning.application.dimensions.base import (
    DimensionResult,
    ReasonerToolkit,
    StrategyOutputKey,
    gather,
)
from reasoning.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from reasoning.domain.request.request import ReasoningContext
from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = ["CompetitiveReasoner"]


class CompetitiveReasoner:
    """Identifies the competitors worth researching, from cited intelligence."""

    name = "competitive"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        return await gather(
            advisor, toolkit, context, ReasoningDimension.COMPETITIVE,
            StrategyOutputKey.COMPETITORS, "What competitors should be researched?",
            limit=6,
        )
