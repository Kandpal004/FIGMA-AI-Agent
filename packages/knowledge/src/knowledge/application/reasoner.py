"""KnowledgeReasoner — the deterministic reasoning core.

This is what turns a corpus into a *reasoning foundation*. Given a
:class:`DecisionContext` — what is being decided — it selects the applicable
principles, ranks them, detects and resolves conflicts, and returns a cited
:class:`Rationale`. It answers the mission's questions directly: *why should this
exist? which UX law / CRO principle / accessibility rule applies? which platform
limitation is in play?*

Every answer is **deterministic and cited**: same context in, same rationale out.
There is no probabilistic retrieval here — selection is structured filtering plus
applicability matching, and ranking is a stable function of priority, confidence,
and specificity. The reasoner performs no I/O of its own; it reads through the
injected :class:`KnowledgeRepository`.
"""

from __future__ import annotations

from knowledge.application.ports.repository import KnowledgeRepository
from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.entry.relation import SUPPORTING_RELATIONS
from knowledge.domain.reasoning.context import DecisionContext
from knowledge.domain.reasoning.query import KnowledgeQuery, SortOrder
from knowledge.domain.reasoning.rationale import Citation, Conflict, Rationale
from knowledge.domain.shared.ids import KnowledgeId
from knowledge.domain.shared.value_objects import Platform
from knowledge.domain.taxonomy.category import KnowledgeCategory

__all__ = ["KnowledgeReasoner"]

# Platform → the category that holds its constraints.
_PLATFORM_CATEGORY: dict[Platform, KnowledgeCategory] = {
    Platform.SHOPIFY_PLUS: KnowledgeCategory.SHOPIFY_PLUS,
    Platform.MAGENTO: KnowledgeCategory.MAGENTO,
}


class KnowledgeReasoner:
    """Selects, ranks, and cites the principles applicable to a decision."""

    def __init__(self, repository: KnowledgeRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------ #
    async def which_apply(
        self, context: DecisionContext, *, tenant_id: object | None = None
    ) -> tuple[KnowledgeEntry, ...]:
        """The ACTIVE principles applicable to ``context``, ranked best-first."""
        query = self._query_for(context, tenant_id)
        matched = await self._repo.find(query)
        applicable = [e for e in matched if self._applies(e, context)]
        applicable.sort(key=query.sort_key, reverse=True)
        return tuple(applicable)

    async def rationale_for(
        self, context: DecisionContext, *, tenant_id: object | None = None
    ) -> Rationale:
        """Build the cited rationale answering the decision ``context``."""
        entries = await self.which_apply(context, tenant_id=tenant_id)
        citations = tuple(
            Citation.from_entry(e, why=self._why(e, context)) for e in entries
        )
        conflicts = self._detect_conflicts(entries)
        aggregate = (
            sum(c.confidence.score for c in citations) / len(citations)
            if citations
            else 0.0
        )
        return Rationale(
            context=context,
            citations=citations,
            conflicts=conflicts,
            aggregate_confidence=aggregate,
            summary=self._summary(context, citations, conflicts),
        )

    async def conflicts(
        self, context: DecisionContext, *, tenant_id: object | None = None
    ) -> tuple[Conflict, ...]:
        """The conflicts among the principles applicable to ``context``."""
        entries = await self.which_apply(context, tenant_id=tenant_id)
        return self._detect_conflicts(entries)

    async def explain(
        self, knowledge_id: KnowledgeId, *, tenant_id: object | None = None
    ) -> Rationale:
        """Explain *why a principle exists* via the principles that support it.

        Uses reverse traversal: the supporting chain is the set of ACTIVE entries
        whose SUPPORTS/REFINES/EXAMPLE_OF/DERIVED_FROM edges point *at* this
        principle — the evidence that justifies it.
        """
        entry = await self._repo.get_active(knowledge_id)
        supporters = await self._repo.find_referencing(
            entry.knowledge_id, SUPPORTING_RELATIONS
        )

        citations = [Citation.from_entry(entry, why="the principle in question")]
        for supporter in supporters:
            relation = next(
                (
                    r
                    for r in supporter.relations
                    if r.target == entry.knowledge_id and r.is_supporting
                ),
                None,
            )
            why = (
                f"{relation.relation_type.value} — {relation.note}".rstrip(" —")
                if relation
                else "supports this principle"
            )
            citations.append(Citation.from_entry(supporter, why=why))

        aggregate = sum(c.confidence.score for c in citations) / len(citations)
        context = DecisionContext(categories=frozenset({entry.category}))
        return Rationale(
            context=context,
            citations=tuple(citations),
            conflicts=(),
            aggregate_confidence=aggregate,
            summary=(
                f"{entry.title!r} is justified by {len(supporters)} supporting "
                f"principle(s)."
            ),
        )

    async def platform_constraints(
        self,
        platform: Platform,
        *,
        context: DecisionContext | None = None,
        tenant_id: object | None = None,
    ) -> tuple[KnowledgeEntry, ...]:
        """The ACTIVE platform-limitation principles for ``platform``."""
        category = _PLATFORM_CATEGORY.get(platform)
        query = KnowledgeQuery(
            categories=frozenset({category}) if category else frozenset(),
            platforms=frozenset({platform}),
            viewer_tenant_id=_as_tenant(tenant_id),
            sort=SortOrder.PRIORITY,
        )
        matched = await self._repo.find(query)
        if context is not None:
            matched = [e for e in matched if self._applies(e, context)]
        ranked = list(matched)
        ranked.sort(key=query.sort_key, reverse=True)
        return tuple(ranked)

    # ------------------------------------------------------------------ #
    def _query_for(
        self, context: DecisionContext, tenant_id: object | None
    ) -> KnowledgeQuery:
        return KnowledgeQuery(
            categories=context.categories,
            platforms=frozenset({context.platform}) if context.platform else frozenset(),
            viewer_tenant_id=_as_tenant(tenant_id),
            sort=SortOrder.RELEVANCE,
        )

    @staticmethod
    def _applies(entry: KnowledgeEntry, context: DecisionContext) -> bool:
        return entry.applies_to(
            page_type=context.page_type,
            component_type=context.component_type,
            platform=context.platform,
            contexts=context.contexts,
        )

    @staticmethod
    def _why(entry: KnowledgeEntry, context: DecisionContext) -> str:
        """A deterministic reason string for why an entry applies."""
        where: list[str] = []
        if context.component_type:
            where.append(f"the {context.component_type}")
        if context.page_type:
            where.append(f"the {context.page_type} page")
        if context.platform:
            where.append(f"on {context.platform.value}")
        scope = " ".join(where) if where else "this decision"
        return f"{entry.category.value} principle applicable to {scope}"

    @staticmethod
    def _detect_conflicts(entries: tuple[KnowledgeEntry, ...]) -> tuple[Conflict, ...]:
        """Find CONTRADICTS edges among the applicable entries and resolve each by
        priority × confidence (deterministic)."""
        by_lineage = {e.knowledge_id: e for e in entries}
        seen: set[frozenset[KnowledgeId]] = set()
        conflicts: list[Conflict] = []
        for entry in entries:
            for relation in entry.relations:
                if not relation.is_conflicting or relation.target not in by_lineage:
                    continue
                pair = frozenset({entry.knowledge_id, relation.target})
                if pair in seen:
                    continue
                seen.add(pair)
                other = by_lineage[relation.target]
                a = Citation.from_entry(entry, why="in tension")
                b = Citation.from_entry(other, why="in tension")
                winner, loser = (a, b) if a.weight >= b.weight else (b, a)
                conflicts.append(
                    Conflict(
                        winner=winner,
                        loser=loser,
                        note=(
                            f"{winner.title!r} outranks {loser.title!r} by "
                            f"priority × confidence."
                        ),
                    )
                )
        return tuple(conflicts)

    @staticmethod
    def _summary(
        context: DecisionContext,
        citations: tuple[Citation, ...],
        conflicts: tuple[Conflict, ...],
    ) -> str:
        if not citations:
            return "No applicable principles found for this context."
        lead = citations[0]
        base = f"{len(citations)} principle(s) apply; primary: {lead.title!r} ({lead.category.value})."
        if conflicts:
            base += f" {len(conflicts)} conflict(s) resolved by priority × confidence."
        return base


def _as_tenant(tenant_id: object | None):
    """Narrow an opaque tenant argument to a UUID or None for query scoping."""
    import uuid

    return tenant_id if isinstance(tenant_id, uuid.UUID) else None
