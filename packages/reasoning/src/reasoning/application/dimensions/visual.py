"""Visual reasoner — design system, typography, spacing, and visual hierarchy.

Produces *directions*, never designs (e.g. "high-contrast serif for editorial
trust"), each grounded in cited knowledge.
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

__all__ = ["VisualReasoner"]


class VisualReasoner:
    """Sets the visual direction across its four facets."""

    name = "visual"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        parts = [
            await gather(advisor, toolkit, context, D.DESIGN_SYSTEM, K.DESIGN_SYSTEM,
                         "What design system should be used?", limit=1),
            await gather(advisor, toolkit, context, D.TYPOGRAPHY, K.TYPOGRAPHY,
                         "What typography direction should be used?", limit=1),
            await gather(advisor, toolkit, context, D.SPACING, K.SPACING,
                         "What spacing philosophy should be used?", limit=1),
            await gather(advisor, toolkit, context, D.VISUAL_HIERARCHY, K.VISUAL_HIERARCHY,
                         "What visual hierarchy should be used?", limit=1),
        ]
        return DimensionResult.merge(*parts)
