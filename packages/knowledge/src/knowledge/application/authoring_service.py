"""KnowledgeAuthoringService — the governed write side of the corpus.

All mutations to knowledge flow through here: authoring a new entry, revising it
into a new version, adding relationship edges, and moving an entry through its
lifecycle. Lifecycle transitions are validated by the
:class:`~knowledge.domain.entry.status.KnowledgeStatusMachine` (illegal moves are
rejected), and each write is atomic via the injected Unit of Work.

The one non-trivial rule enforced here is **single-active-per-lineage**: activating
a version supersedes any prior ACTIVE version of the same lineage, so the corpus
always has exactly one servable version of a principle. Timestamps come from the
injected clock; there is no global state.
"""

from __future__ import annotations

from core.errors import NotFoundError

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
from knowledge.application.ports.clock import Clock
from knowledge.application.ports.unit_of_work import UnitOfWorkFactory
from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.entry.relation import KnowledgeRelation
from knowledge.domain.entry.status import KnowledgeStatus, KnowledgeStatusMachine
from knowledge.domain.shared.ids import EntryVersionId, RelationId

__all__ = ["KnowledgeAuthoringService"]


class KnowledgeAuthoringService:
    """Authors and curates knowledge under a governed lifecycle."""

    def __init__(
        self,
        *,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        status_machine: KnowledgeStatusMachine | None = None,
    ) -> None:
        self._uow = unit_of_work_factory
        self._clock = clock
        self._machine = status_machine or KnowledgeStatusMachine()

    # -- authoring --------------------------------------------------------- #
    async def add(self, command: AddEntry) -> KnowledgeEntry:
        """Author a new v1 DRAFT entry and persist it."""
        entry = KnowledgeEntry.create(
            category=command.category,
            title=command.title,
            statement=command.statement,
            description=command.description,
            source=command.source,
            at=self._clock.now(),
            knowledge_id=command.knowledge_id,
            subcategory=command.subcategory,
            confidence=command.confidence,
            priority=command.priority,
            applicability=command.applicability,
            tags=command.tags,
            references=command.references,
            scope=command.scope,
        )
        async with self._uow() as uow:
            await uow.entries.save(entry)
            await uow.commit()
        return entry

    async def revise(self, command: ReviseEntry) -> KnowledgeEntry:
        """Create the next DRAFT version of a lineage from an existing version."""
        async with self._uow() as uow:
            base = await uow.entries.get(command.from_entry_version_id)
            revised = base.revise(
                at=self._clock.now(),
                title=command.title,
                statement=command.statement,
                description=command.description,
                confidence=command.confidence,
                priority=command.priority,
                applicability=command.applicability,
                subcategory=command.subcategory,
                tags=command.tags,
                references=command.references,
            )
            await uow.entries.save(revised)
            await uow.commit()
        return revised

    async def add_relation(self, command: AddRelation) -> KnowledgeEntry:
        """Attach a typed relationship edge to an entry version."""
        async with self._uow() as uow:
            entry = await uow.entries.get(command.entry_version_id)
            relation = KnowledgeRelation(
                id=RelationId.new(),
                relation_type=command.relation_type,
                target=command.target,
                note=command.note,
            )
            updated = entry.add_relation(relation, at=self._clock.now())
            await uow.entries.save(updated)
            await uow.commit()
        return updated

    # -- lifecycle --------------------------------------------------------- #
    async def propose(self, command: ProposeEntry) -> KnowledgeEntry:
        """DRAFT → PROPOSED."""
        return await self._set_status(command.entry_version_id, KnowledgeStatus.PROPOSED)

    async def reject(self, command: RejectEntry) -> KnowledgeEntry:
        """PROPOSED → DRAFT."""
        return await self._set_status(command.entry_version_id, KnowledgeStatus.DRAFT)

    async def activate(self, command: ActivateEntry) -> KnowledgeEntry:
        """PROPOSED → ACTIVE, superseding any prior ACTIVE version of the lineage."""
        return await self._set_status(
            command.entry_version_id, KnowledgeStatus.ACTIVE, supersede_prior=True
        )

    async def deprecate(self, command: DeprecateEntry) -> KnowledgeEntry:
        """ACTIVE → DEPRECATED."""
        return await self._set_status(
            command.entry_version_id, KnowledgeStatus.DEPRECATED
        )

    async def reinstate(self, command: ReinstateEntry) -> KnowledgeEntry:
        """DEPRECATED → ACTIVE, superseding any other ACTIVE version."""
        return await self._set_status(
            command.entry_version_id, KnowledgeStatus.ACTIVE, supersede_prior=True
        )

    async def archive(self, command: ArchiveEntry) -> KnowledgeEntry:
        """→ ARCHIVED."""
        return await self._set_status(command.entry_version_id, KnowledgeStatus.ARCHIVED)

    # -- internal ---------------------------------------------------------- #
    async def _set_status(
        self,
        entry_version_id: EntryVersionId,
        target: KnowledgeStatus,
        *,
        supersede_prior: bool = False,
    ) -> KnowledgeEntry:
        async with self._uow() as uow:
            entry = await uow.entries.get(entry_version_id)
            self._machine.validate(entry.status, target)
            now = self._clock.now()

            if supersede_prior:
                prior = await self._current_active(uow, entry)
                if prior is not None and prior.id != entry.id:
                    await uow.entries.save(
                        prior.with_status(KnowledgeStatus.SUPERSEDED, at=now)
                    )

            updated = entry.with_status(target, at=now)
            await uow.entries.save(updated)
            await uow.commit()
        return updated

    @staticmethod
    async def _current_active(uow: object, entry: KnowledgeEntry) -> KnowledgeEntry | None:
        try:
            return await uow.entries.get_active(entry.knowledge_id)  # type: ignore[attr-defined]
        except NotFoundError:
            return None
