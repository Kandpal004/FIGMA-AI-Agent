"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the six signal ports, the composer, a clock), wires
the SQLAlchemy unit of work into the engine and facade. Kept apart from the in-memory container so
in-memory usage need not depend on SQLAlchemy. Imports no Figma SDK, MCP client, or HTTP library.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from figma_design.application.figma_design_engine import FigmaDesignEngine
from figma_design.application.ports.clock import Clock
from figma_design.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from figma_design.application.ports.creative_director_input import CreativeDirectorInputPort
from figma_design.application.ports.design_language_input import DesignLanguageInputPort
from figma_design.application.ports.design_orchestrator_input import DesignOrchestratorInputPort
from figma_design.application.ports.design_system_input import DesignSystemInputPort
from figma_design.application.ports.figma_composer import FigmaComposerPort
from figma_design.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from figma_design.infrastructure.adapters.inmemory_inputs import (
    NullComponentIntelligenceInput,
    NullCreativeDirectorInput,
    NullDesignLanguageInput,
    NullDesignOrchestratorInput,
    NullDesignSystemInput,
    NullKnowledgeAdvisor,
)
from figma_design.infrastructure.adapters.rule_based_figma_composer import RuleBasedFigmaComposer
from figma_design.infrastructure.container import build_engine, build_facade
from figma_design.infrastructure.inmemory import SystemClock
from figma_design.infrastructure.persistence.models import Base
from figma_design.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from figma_design.interfaces.figma_design_facade import FigmaDesignFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: FigmaDesignFacade
    engine: FigmaDesignEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    design_orchestrator: DesignOrchestratorInputPort | None = None,
    design_system: DesignSystemInputPort | None = None,
    component_intelligence: ComponentIntelligenceInputPort | None = None,
    design_language: DesignLanguageInputPort | None = None,
    creative_director: CreativeDirectorInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    composer: FigmaComposerPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        design_orchestrator=design_orchestrator or NullDesignOrchestratorInput(),
        design_system=design_system or NullDesignSystemInput(),
        component_intelligence=component_intelligence or NullComponentIntelligenceInput(),
        design_language=design_language or NullDesignLanguageInput(),
        creative_director=creative_director or NullCreativeDirectorInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        composer=composer or RuleBasedFigmaComposer(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the figma-design tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
