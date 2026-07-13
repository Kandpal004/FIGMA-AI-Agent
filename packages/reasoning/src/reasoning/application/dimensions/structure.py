"""Structure reasoner — which sections should exist (required/optional/removed).

Each cited structure principle becomes a :class:`SectionRecommendation` and an
explicit, scored decision to include the section — so section choices live in the
decision graph and can be risk-assessed. A silent corpus yields a knowledge gap,
not invented sections.
"""

from __future__ import annotations

import re

from reasoning.application.dimensions.base import (
    DimensionResult,
    ReasonerToolkit,
)
from reasoning.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from reasoning.domain.request.request import ReasoningContext
from reasoning.domain.shared.value_objects import ReasoningDimension
from reasoning.domain.strategy.structure import SectionStatus

__all__ = ["StructureReasoner"]

_SLUG = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG.sub("-", text.strip().lower()).strip("-") or "section"


class StructureReasoner:
    """Determines the page's section structure from cited knowledge."""

    name = "structure"

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        req = context.request
        principles = await advisor.advise(
            ReasoningDimension.STRUCTURE,
            page_type=req.page_type,
            component_type=req.component_type,
            platform=req.platform,
            contexts=req.contexts,
            tenant_id=context.tenant_id,
            limit=12,
        )
        if not principles:
            return DimensionResult(
                gaps=(toolkit.gap(ReasoningDimension.STRUCTURE, "What sections should exist?"),)
            )

        evidence = []
        reasons = []
        sections = []
        decisions = []
        seen: set[str] = set()
        for index, principle in enumerate(principles):
            name = _slug(principle.title)
            if name in seen:  # keep section names unique
                continue
            seen.add(name)
            ref = toolkit.evidence(principle, ReasoningDimension.STRUCTURE)
            reason = toolkit.reason(
                ReasoningDimension.STRUCTURE, "What sections should exist?",
                principle.statement, confidence=principle.confidence, evidence_ids=(ref.id,),
            )
            section = toolkit.section(
                name, SectionStatus.REQUIRED, principle.statement,
                evidence_ids=(ref.id,), confidence=principle.confidence, order=index,
            )
            chosen = toolkit.option(f"include {name}", evidence_ids=(ref.id,), score=principle.confidence * 100)
            decision = toolkit.decision(
                ReasoningDimension.STRUCTURE, f"Include the {name} section?",
                chosen, confidence=principle.confidence, reason_ids=(reason.id,),
            )
            evidence.append(ref)
            reasons.append(reason)
            sections.append(section)
            decisions.append(decision)

        return DimensionResult(
            evidence=tuple(evidence),
            reasons=tuple(reasons),
            decisions=tuple(decisions),
            sections=tuple(sections),
        )
