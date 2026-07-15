"""Composition root — wire the real engines, the executor, the Director, and a seeded project.

This is the one place the Homepage workflow's concrete parts meet. It builds the shared Phase-3
Knowledge environment (and seeds it with a few homepage principles so the knowledge-grounded engines
have something to reason over), constructs the :class:`EngineAgentExecutor` over it, stands up the
**Director (Phase 2)** in-memory environment wired with that executor and the homepage-only workflow
catalog, and seeds a project with a homepage page-section for the run to design.

Nothing here is a new engine or abstraction — it is pure wiring. The returned
:class:`HomepageEnvironment` hands the caller everything needed to drive and inspect a run.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

# --- Phase 3: Knowledge ----------------------------------------------------- #
from knowledge.application.commands import ActivateEntry, AddEntry, ProposeEntry
from knowledge.application.query_service import KnowledgeQueryService
from knowledge.domain.entry.source import Source, SourceKind
from knowledge.domain.shared.ids import EntryVersionId
from knowledge.domain.shared.value_objects import Confidence as KConfidence, Priority as KPriority
from knowledge.domain.taxonomy.category import KnowledgeCategory
from knowledge.infrastructure.container import build_in_memory_environment as build_knowledge
from knowledge.infrastructure.inmemory import InMemoryKnowledgeSearchPort

# --- Phase 2: Director ------------------------------------------------------ #
from director.domain.project.entities import Project, Section
from director.domain.shared.ids import ProjectId, SectionId
from director.domain.shared.value_objects import PageType
from director.infrastructure.container import (
    DirectorEnvironment,
    build_in_memory_environment as build_director_env,
)
from director.interfaces.director_facade import DirectorFacade

from homepage_workflow.definition import build_homepage_catalog
from homepage_workflow.engine_executor import EngineAgentExecutor

__all__ = ["HomepageEnvironment", "build_homepage_environment"]

#: The section key representing the homepage itself.
HOMEPAGE_SECTION_KEY = "homepage"

# The canonical homepage design principle seeded into the knowledge base. A single, high-signal
# entry is deliberate: it grounds every knowledge-consuming engine without a topic search ever
# returning a tie the knowledge ranker cannot break — the same configuration the platform's
# integration suite runs against.
_SEED_PRINCIPLES: tuple[tuple[KnowledgeCategory, str, str], ...] = (
    (
        KnowledgeCategory.CONVERSION_OPTIMIZATION,
        "Homepage clarity, trust, then conversion",
        "A premium homepage states its value proposition with one primary call to action above the "
        "fold, places trust signals — reviews, guarantees, social proof — before the conversion "
        "ask, and uses a restrained, high-contrast editorial type scale to signal quality.",
    ),
)


@dataclass(frozen=True, slots=True)
class HomepageEnvironment:
    """Everything needed to drive and inspect a homepage run.

    Attributes:
        facade: The Director facade — start/resume/approve/reject/inspect runs.
        director_env: The full Director in-memory environment (storage, memory, uow).
        knowledge_query: The shared Phase-3 knowledge query service.
        executor: The engine executor behind the Director's agent-executor port.
        tenant_id: The seeded tenant.
        project_id: The seeded project.
        page_section_id: The homepage page-section the run designs.
    """

    facade: DirectorFacade
    director_env: DirectorEnvironment
    knowledge_query: KnowledgeQueryService
    executor: EngineAgentExecutor
    tenant_id: uuid.UUID
    project_id: ProjectId
    page_section_id: SectionId


async def _seed_knowledge(query_env) -> None:
    for category, title, statement in _SEED_PRINCIPLES:
        view = await query_env.facade.add(AddEntry(
            category=category,
            title=title,
            statement=statement,
            description="Seeded homepage principle.",
            source=Source(name="Nielsen Norman Group", kind=SourceKind.RESEARCH_INSTITUTE),
            confidence=KConfidence.of(0.9),
            priority=KPriority.HIGH,
        ))
        vid = EntryVersionId.from_string(view.entry_version_id)
        await query_env.facade.propose(ProposeEntry(entry_version_id=vid))
        await query_env.facade.activate(ActivateEntry(entry_version_id=vid))


async def build_homepage_environment(
    *,
    tenant_id: uuid.UUID | None = None,
    project_name: str = "Homepage Design",
    seed_knowledge: bool = True,
    max_redesigns: int = 3,
) -> HomepageEnvironment:
    """Wire the real engines, the executor, and the Director, and seed a homepage project.

    Args:
        tenant_id: The owning tenant (a fresh UUID if not supplied).
        project_name: The seeded project's name.
        seed_knowledge: Whether to seed the knowledge base with homepage principles.
        max_redesigns: The Director's redesign guard rail.

    Returns:
        A fully wired :class:`HomepageEnvironment`.
    """
    tenant = tenant_id or uuid.uuid4()

    # 1. Shared knowledge (Phase 3).
    knowledge_env = build_knowledge()
    if seed_knowledge:
        await _seed_knowledge(knowledge_env)
    query = KnowledgeQueryService(
        knowledge_env.repository, InMemoryKnowledgeSearchPort(knowledge_env.storage)
    )

    # 2. The engine executor over the shared knowledge.
    executor = EngineAgentExecutor(query)

    # 3. The Director, wired with the executor and the homepage-only catalog.
    director_env = build_director_env(
        executor, catalog=build_homepage_catalog(), max_redesigns=max_redesigns
    )

    # 4. Seed a project with a homepage page-section.
    project_id = ProjectId.new()
    section = Section(
        id=SectionId.new(), key=HOMEPAGE_SECTION_KEY, page_type=PageType.HOMEPAGE, title="Homepage"
    )
    project = Project(id=project_id, tenant_id=tenant, name=project_name, sections=(section,))
    director_env.storage.projects[project_id] = project

    return HomepageEnvironment(
        facade=director_env.facade,
        director_env=director_env,
        knowledge_query=query,
        executor=executor,
        tenant_id=tenant,
        project_id=project_id,
        page_section_id=section.id,
    )
