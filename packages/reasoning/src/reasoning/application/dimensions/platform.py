"""Platform reasoner — which Shopify or Magento constraints apply.

Constraints are queried against the ``PLATFORM_CONSTRAINTS`` dimension but routed
to the platform-specific output key. When no platform is specified (agnostic), the
reasoner contributes nothing — there is no constraint to cite, and absence of a
platform is not a knowledge gap.
"""

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

__all__ = ["PlatformReasoner"]

_PLATFORM_OUTPUT = {
    "shopify_plus": (StrategyOutputKey.SHOPIFY_CONSTRAINTS, "What Shopify constraints apply?"),
    "magento": (StrategyOutputKey.MAGENTO_CONSTRAINTS, "What Magento constraints apply?"),
}


class PlatformReasoner:
    """Selects the platform limitations the design must respect."""

    name = "platform"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        platform = context.request.platform
        mapping = _PLATFORM_OUTPUT.get(platform or "")
        if mapping is None:
            return DimensionResult()  # agnostic / unspecified — no constraints to cite
        output_key, question = mapping
        return await gather(
            advisor, toolkit, context, ReasoningDimension.PLATFORM_CONSTRAINTS,
            output_key, question, limit=6,
        )
