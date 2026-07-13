"""The Knowledge facade — the inbound entry point of the engine.

The single surface everything above the engine calls: agents, the Director, a
future API or MCP tool. It exposes reasoning ("ask", "explain", "which apply",
"platform constraints"), structured querying, and the governed authoring lifecycle,
and returns serializable views — never raw domain aggregates. It owns no logic of
its own; it delegates to the reasoner, query service, and authoring service.
"""

from __future__ import annotations

from knowledge.application.authoring_service import KnowledgeAuthoringService
from knowledge.application.commands import (
    ActivateEntry,
    AddEntry,
    AddRelation,
    ArchiveEntry,
    DeprecateEntry,
    ProposeEntry,
    ReinstateEntry,
    RejectEntry,
    ReviseEntry,
)
from knowledge.application.query_service import KnowledgeQueryService
from knowledge.application.reasoner import KnowledgeReasoner
from knowledge.domain.reasoning.context import DecisionContext
from knowledge.domain.reasoning.query import KnowledgeQuery
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId
from knowledge.domain.shared.value_objects import Platform
from knowledge.interfaces.dto import (
    EntryView,
    NeighborhoodView,
    QueryResultView,
    RationaleView,
)

__all__ = ["KnowledgeFacade"]


class KnowledgeFacade:
    """Reasoning, querying, and authoring — commands in, views out."""

    def __init__(
        self,
        *,
        reasoner: KnowledgeReasoner,
        query_service: KnowledgeQueryService,
        authoring_service: KnowledgeAuthoringService,
    ) -> None:
        self._reasoner = reasoner
        self._query = query_service
        self._authoring = authoring_service

    # -- reasoning --------------------------------------------------------- #
    async def ask(
        self, context: DecisionContext, *, tenant_id: object | None = None
    ) -> RationaleView:
        """The cited rationale answering a decision context."""
        rationale = await self._reasoner.rationale_for(context, tenant_id=tenant_id)
        return RationaleView.from_rationale(rationale)

    async def which_apply(
        self, context: DecisionContext, *, tenant_id: object | None = None
    ) -> list[EntryView]:
        """The ranked principles applicable to a context."""
        entries = await self._reasoner.which_apply(context, tenant_id=tenant_id)
        return [EntryView.from_entry(e) for e in entries]

    async def explain(
        self, knowledge_id: KnowledgeId, *, tenant_id: object | None = None
    ) -> RationaleView:
        """Why a specific principle exists, via its supporting chain."""
        rationale = await self._reasoner.explain(knowledge_id, tenant_id=tenant_id)
        return RationaleView.from_rationale(rationale)

    async def platform_constraints(
        self, platform: Platform, *, tenant_id: object | None = None
    ) -> list[EntryView]:
        """The platform-limitation principles for a platform."""
        entries = await self._reasoner.platform_constraints(platform, tenant_id=tenant_id)
        return [EntryView.from_entry(e) for e in entries]

    # -- querying ---------------------------------------------------------- #
    async def query(self, query: KnowledgeQuery) -> QueryResultView:
        """Structured retrieval."""
        return QueryResultView.from_result(await self._query.find(query))

    async def search(self, text: str, *, query: KnowledgeQuery | None = None) -> QueryResultView:
        """Free-text search (semantic when available, else structured)."""
        return QueryResultView.from_result(await self._query.search(text, query=query))

    async def get(self, entry_version_id: EntryVersionId) -> EntryView:
        """One exact version."""
        return EntryView.from_entry(await self._query.get(entry_version_id))

    async def get_active(self, knowledge_id: KnowledgeId) -> EntryView:
        """The current ACTIVE version of a lineage."""
        return EntryView.from_entry(await self._query.get_active(knowledge_id))

    async def history(self, knowledge_id: KnowledgeId) -> list[EntryView]:
        """Every version of a lineage, oldest first."""
        return [EntryView.from_entry(e) for e in await self._query.history(knowledge_id)]

    async def neighborhood(self, knowledge_id: KnowledgeId) -> NeighborhoodView:
        """An entry's directly related principles."""
        return NeighborhoodView.from_neighborhood(
            await self._query.neighborhood(knowledge_id)
        )

    # -- authoring lifecycle ---------------------------------------------- #
    async def add(self, command: AddEntry) -> EntryView:
        return EntryView.from_entry(await self._authoring.add(command))

    async def revise(self, command: ReviseEntry) -> EntryView:
        return EntryView.from_entry(await self._authoring.revise(command))

    async def add_relation(self, command: AddRelation) -> EntryView:
        return EntryView.from_entry(await self._authoring.add_relation(command))

    async def propose(self, command: ProposeEntry) -> EntryView:
        return EntryView.from_entry(await self._authoring.propose(command))

    async def activate(self, command: ActivateEntry) -> EntryView:
        return EntryView.from_entry(await self._authoring.activate(command))

    async def reject(self, command: RejectEntry) -> EntryView:
        return EntryView.from_entry(await self._authoring.reject(command))

    async def deprecate(self, command: DeprecateEntry) -> EntryView:
        return EntryView.from_entry(await self._authoring.deprecate(command))

    async def reinstate(self, command: ReinstateEntry) -> EntryView:
        return EntryView.from_entry(await self._authoring.reinstate(command))

    async def archive(self, command: ArchiveEntry) -> EntryView:
        return EntryView.from_entry(await self._authoring.archive(command))
