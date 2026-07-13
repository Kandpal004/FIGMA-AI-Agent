"""Review reasoner — what the Creative Director should review."""

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

__all__ = ["ReviewReasoner"]


class ReviewReasoner:
    """Determines the points the Creative Director should review."""

    name = "review"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        return await gather(
            advisor, toolkit, context, ReasoningDimension.CREATIVE_REVIEW,
            StrategyOutputKey.REVIEW_POINTS,
            "What should the Creative Director review?", limit=5,
        )
