"""Customer reasoner — who the customer is, and what moves them.

Answers: who is the customer, the target market, their problems, objections,
emotional triggers, and required trust mechanisms — each grounded in cited
knowledge.
"""

from __future__ import annotations

from reasoning.application.dimensions.base import (
    DimensionResult,
    ReasonerToolkit,
    StrategyOutputKey as K,
    gather,
)
from reasoning.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from reasoning.domain.request.request import ReasoningContext
from reasoning.domain.shared.value_objects import ReasoningDimension as D

__all__ = ["CustomerReasoner"]


class CustomerReasoner:
    """Builds the customer profile across its six facets."""

    name = "customer"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        parts = [
            await gather(advisor, toolkit, context, D.CUSTOMER, K.CUSTOMER_WHO,
                         "Who is the customer?", limit=1),
            await gather(advisor, toolkit, context, D.TARGET_MARKET, K.TARGET_MARKET,
                         "What is the target market?", limit=1),
            await gather(advisor, toolkit, context, D.CUSTOMER_PROBLEMS, K.PROBLEMS,
                         "What customer problems exist?", limit=4),
            await gather(advisor, toolkit, context, D.OBJECTIONS, K.OBJECTIONS,
                         "What objections exist?", limit=4),
            await gather(advisor, toolkit, context, D.EMOTIONAL_TRIGGERS, K.EMOTIONAL_TRIGGERS,
                         "What emotional triggers should be used?", limit=4),
            await gather(advisor, toolkit, context, D.TRUST_MECHANISMS, K.TRUST_MECHANISMS,
                         "What trust mechanisms are required?", limit=4),
        ]
        return DimensionResult.merge(*parts)
