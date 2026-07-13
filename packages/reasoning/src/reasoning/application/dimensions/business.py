"""Business reasoner — answers "what is the business objective?"."""

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

__all__ = ["BusinessReasoner"]


class BusinessReasoner:
    """Determines the business objective the design must serve."""

    name = "business"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        return await gather(
            advisor,
            toolkit,
            context,
            ReasoningDimension.BUSINESS,
            StrategyOutputKey.BUSINESS_OBJECTIVE,
            "What is the business objective?",
            limit=2,
        )
