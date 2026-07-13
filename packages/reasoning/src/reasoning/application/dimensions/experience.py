"""Experience reasoner — which UX principles and accessibility rules apply."""

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

__all__ = ["ExperienceReasoner"]


class ExperienceReasoner:
    """Selects the UX principles and accessibility rules that apply."""

    name = "experience"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        ux = await gather(advisor, toolkit, context, D.USER_EXPERIENCE, K.UX_PRINCIPLES,
                          "What UX principles apply?", limit=5)
        a11y = await gather(advisor, toolkit, context, D.ACCESSIBILITY, K.ACCESSIBILITY_RULES,
                            "What accessibility rules apply?", limit=5)
        return DimensionResult.merge(ux, a11y)
