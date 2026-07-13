"""KnowledgeAdvisorAdapter — bridges the reasoning engine to the Knowledge Engine.

This is the single place the two phases meet. It implements the reasoning-owned
:class:`KnowledgeAdvisorPort` by translating a :class:`ReasoningDimension` into the
right Phase-3 knowledge category, building a Phase-3 :class:`DecisionContext`, and
calling the Phase-3 :class:`KnowledgeReasoner` for the applicable, cited entries —
which it maps back into decoupled :class:`AdvisedPrinciple` DTOs.

Because this mapping lives here, the reasoning application never imports the
Knowledge Engine; swapping how knowledge is sourced (a different corpus, a remote
service) is a change to this adapter alone.
"""

from __future__ import annotations

from collections.abc import Sequence

from knowledge.application.reasoner import KnowledgeReasoner
from knowledge.domain.reasoning.context import DecisionContext
from knowledge.domain.shared.value_objects import Platform as KPlatform, Tag
from knowledge.domain.taxonomy.category import KnowledgeCategory

from reasoning.application.ports.knowledge_advisor import AdvisedPrinciple
from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = ["KnowledgeAdvisorAdapter"]

# Reasoning dimension → the knowledge category that holds its principles.
_DIMENSION_CATEGORY: dict[ReasoningDimension, KnowledgeCategory] = {
    ReasoningDimension.BUSINESS: KnowledgeCategory.BUSINESS,
    ReasoningDimension.CUSTOMER: KnowledgeCategory.CUSTOMER_PSYCHOLOGY,
    ReasoningDimension.TARGET_MARKET: KnowledgeCategory.BUSINESS,
    ReasoningDimension.CUSTOMER_PROBLEMS: KnowledgeCategory.CUSTOMER_PSYCHOLOGY,
    ReasoningDimension.OBJECTIONS: KnowledgeCategory.CONVERSION_OPTIMIZATION,
    ReasoningDimension.EMOTIONAL_TRIGGERS: KnowledgeCategory.CUSTOMER_PSYCHOLOGY,
    ReasoningDimension.TRUST_MECHANISMS: KnowledgeCategory.CONVERSION_OPTIMIZATION,
    ReasoningDimension.CONVERSION: KnowledgeCategory.CONVERSION_OPTIMIZATION,
    ReasoningDimension.USER_EXPERIENCE: KnowledgeCategory.UX_LAWS,
    ReasoningDimension.ACCESSIBILITY: KnowledgeCategory.ACCESSIBILITY,
    ReasoningDimension.COMPETITIVE: KnowledgeCategory.COMPETITOR_INTELLIGENCE,
    ReasoningDimension.DESIGN_SYSTEM: KnowledgeCategory.DESIGN_SYSTEM,
    ReasoningDimension.TYPOGRAPHY: KnowledgeCategory.TYPOGRAPHY,
    ReasoningDimension.SPACING: KnowledgeCategory.SPACING,
    ReasoningDimension.VISUAL_HIERARCHY: KnowledgeCategory.VISUAL_HIERARCHY,
    ReasoningDimension.STRUCTURE: KnowledgeCategory.DESIGN_PRINCIPLES,
    ReasoningDimension.CREATIVE_REVIEW: KnowledgeCategory.CREATIVE_DIRECTION,
}

_PLATFORM_MAP: dict[str, KPlatform] = {
    "shopify_plus": KPlatform.SHOPIFY_PLUS,
    "magento": KPlatform.MAGENTO,
    "agnostic": KPlatform.AGNOSTIC,
}


class KnowledgeAdvisorAdapter:
    """Implements :class:`KnowledgeAdvisorPort` over the Phase-3 reasoner."""

    def __init__(self, reasoner: KnowledgeReasoner) -> None:
        self._reasoner = reasoner

    async def advise(
        self,
        dimension: ReasoningDimension,
        *,
        page_type: str | None = None,
        component_type: str | None = None,
        platform: str | None = None,
        contexts: Sequence[str] = (),
        tenant_id: object | None = None,
        limit: int | None = None,
    ) -> Sequence[AdvisedPrinciple]:
        category = self._category_for(dimension, platform)
        k_platform = _PLATFORM_MAP.get(platform or "")
        knowledge_context = DecisionContext(
            categories=frozenset({category}) if category else frozenset(),
            page_type=page_type,
            component_type=component_type,
            platform=k_platform,
            contexts=frozenset(Tag.of(c) for c in contexts),
        )
        entries = await self._reasoner.which_apply(knowledge_context, tenant_id=tenant_id)
        principles = [
            AdvisedPrinciple(
                knowledge_id=str(entry.knowledge_id),
                entry_version_id=str(entry.id),
                category=entry.category.value,
                title=entry.title,
                statement=entry.statement,
                source_name=entry.source.name,
                confidence=entry.confidence.score,
                relevance=f"applies to {dimension.value}",
            )
            for entry in entries
        ]
        return principles[:limit] if limit is not None else principles

    @staticmethod
    def _category_for(
        dimension: ReasoningDimension, platform: str | None
    ) -> KnowledgeCategory | None:
        if dimension is ReasoningDimension.PLATFORM_CONSTRAINTS:
            if platform == "shopify_plus":
                return KnowledgeCategory.SHOPIFY_PLUS
            if platform == "magento":
                return KnowledgeCategory.MAGENTO
            return None
        return _DIMENSION_CATEGORY.get(dimension)
