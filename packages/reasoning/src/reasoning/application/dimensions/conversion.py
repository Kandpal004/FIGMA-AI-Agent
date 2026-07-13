"""Conversion reasoner — which CRO principles apply, and the resulting decision.

Beyond listing the applicable CRO principles, this reasoner makes an explicit,
cited *decision* about how to optimise conversion — so the choice appears in the
decision graph, is scored, and can be risk-assessed.
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

__all__ = ["ConversionReasoner"]


class ConversionReasoner:
    """Selects the CRO principles and decides the conversion approach."""

    name = "conversion"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        result = await gather(
            advisor, toolkit, context, ReasoningDimension.CONVERSION,
            StrategyOutputKey.CRO_PRINCIPLES, "What CRO principles apply?", limit=5,
        )
        principles = result.get(StrategyOutputKey.CRO_PRINCIPLES)
        if not principles:
            return result

        top = principles[0]
        chosen = toolkit.option(
            f"Prioritise conversion via: {top.statement}",
            evidence_ids=top.evidence_ids, score=round(top.confidence * 100, 2),
        )
        # Runner-up principles become the considered-and-rejected alternatives,
        # so the decision records a genuine trade-off.
        considered = [
            toolkit.option(
                f"Alternatively: {alt.statement}",
                evidence_ids=alt.evidence_ids, score=round(alt.confidence * 100, 2),
            )
            for alt in principles[1:]
        ]
        reason_ids = (top.reason_id,) if top.reason_id is not None else ()
        decision = toolkit.decision(
            ReasoningDimension.CONVERSION, "How should conversion be optimised?",
            chosen, confidence=top.confidence, considered=considered, reason_ids=reason_ids,
        )
        return DimensionResult.merge(result, DimensionResult(decisions=(decision,)))
