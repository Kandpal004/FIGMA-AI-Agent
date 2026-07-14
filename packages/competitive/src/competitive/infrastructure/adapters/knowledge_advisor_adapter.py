"""KnowledgeAdvisorAdapter — grounds the intelligence engine in the Knowledge Engine.

The single seam where Phase 5 meets Phase 3. It maps a
:class:`~competitive.domain.shared.value_objects.CompetitorDimension` to the right
Phase-3 knowledge category, builds a Phase-3 :class:`DecisionContext`, and calls the
Phase-3 :class:`KnowledgeReasoner` for the applicable, cited entries — mapping them
back into decoupled :class:`AdvisedPrinciple` DTOs. The engine never imports Phase 3.
"""

from __future__ import annotations

from collections.abc import Sequence

from knowledge.application.reasoner import KnowledgeReasoner
from knowledge.domain.reasoning.context import DecisionContext
from knowledge.domain.shared.value_objects import Tag
from knowledge.domain.taxonomy.category import KnowledgeCategory

from competitive.application.ports.knowledge_advisor import AdvisedPrinciple
from competitive.domain.shared.value_objects import CompetitorDimension as Dim

__all__ = ["KnowledgeAdvisorAdapter"]

_DIMENSION_CATEGORY: dict[Dim, KnowledgeCategory] = {
    Dim.BRAND_POSITIONING: KnowledgeCategory.BUSINESS,
    Dim.VISUAL_LANGUAGE: KnowledgeCategory.DESIGN_PRINCIPLES,
    Dim.TYPOGRAPHY: KnowledgeCategory.TYPOGRAPHY,
    Dim.SPACING: KnowledgeCategory.SPACING,
    Dim.NAVIGATION: KnowledgeCategory.UX_LAWS,
    Dim.INFORMATION_ARCHITECTURE: KnowledgeCategory.UX_LAWS,
    Dim.HOMEPAGE_STRUCTURE: KnowledgeCategory.DESIGN_PRINCIPLES,
    Dim.COLLECTION_STRATEGY: KnowledgeCategory.CONVERSION_OPTIMIZATION,
    Dim.PRODUCT_PAGE_STRATEGY: KnowledgeCategory.CONVERSION_OPTIMIZATION,
    Dim.TRUST_STRATEGY: KnowledgeCategory.CONVERSION_OPTIMIZATION,
    Dim.CHECKOUT_STRATEGY: KnowledgeCategory.CONVERSION_OPTIMIZATION,
    Dim.MOBILE_STRATEGY: KnowledgeCategory.UX_LAWS,
    Dim.ACCESSIBILITY: KnowledgeCategory.ACCESSIBILITY,
    Dim.PERFORMANCE: KnowledgeCategory.PERFORMANCE,
    Dim.SEO: KnowledgeCategory.SEO,
    Dim.CONVERSION_PATTERNS: KnowledgeCategory.CONVERSION_OPTIMIZATION,
}


class KnowledgeAdvisorAdapter:
    """Implements :class:`KnowledgeAdvisorPort` over the Phase-3 reasoner."""

    def __init__(self, reasoner: KnowledgeReasoner) -> None:
        self._reasoner = reasoner

    async def advise(
        self,
        dimension: Dim,
        *,
        industry: str | None = None,
        market: str | None = None,
        contexts: Sequence[str] = (),
        tenant_id: object | None = None,
        limit: int | None = None,
    ) -> Sequence[AdvisedPrinciple]:
        category = _DIMENSION_CATEGORY.get(dimension)
        knowledge_context = DecisionContext(
            categories=frozenset({category}) if category else frozenset(),
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
                relevance=f"grounds {dimension.value}",
            )
            for entry in entries
        ]
        return principles[:limit] if limit is not None else principles
