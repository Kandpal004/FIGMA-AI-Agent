"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the eleven signal ports, the planner, a clock),
wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the in-memory
container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from design_orchestrator.application.design_orchestrator_engine import DesignOrchestratorEngine
from design_orchestrator.application.ports.brand_input import BrandInputPort
from design_orchestrator.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_orchestrator.application.ports.clock import Clock
from design_orchestrator.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from design_orchestrator.application.ports.creative_director_input import CreativeDirectorInputPort
from design_orchestrator.application.ports.design_language_input import DesignLanguageInputPort
from design_orchestrator.application.ports.design_system_input import DesignSystemInputPort
from design_orchestrator.application.ports.execution_planner import ExecutionPlannerPort
from design_orchestrator.application.ports.ia_input import IAInputPort
from design_orchestrator.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_orchestrator.application.ports.psychology_input import PsychologyInputPort
from design_orchestrator.application.ports.ux_input import UXInputPort
from design_orchestrator.application.ports.wireframe_input import WireframeInputPort
from design_orchestrator.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullComponentIntelligenceInput,
    NullCreativeDirectorInput,
    NullDesignLanguageInput,
    NullDesignSystemInput,
    NullIAInput,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullUXInput,
    NullWireframeInput,
)
from design_orchestrator.infrastructure.adapters.rule_based_execution_planner import (
    RuleBasedExecutionPlanner,
)
from design_orchestrator.infrastructure.container import build_engine, build_facade
from design_orchestrator.infrastructure.inmemory import SystemClock
from design_orchestrator.infrastructure.persistence.models import Base
from design_orchestrator.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from design_orchestrator.interfaces.design_orchestrator_facade import DesignOrchestratorFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: DesignOrchestratorFacade
    engine: DesignOrchestratorEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    design_system: DesignSystemInputPort | None = None,
    component_intelligence: ComponentIntelligenceInputPort | None = None,
    wireframe: WireframeInputPort | None = None,
    creative_director: CreativeDirectorInputPort | None = None,
    design_language: DesignLanguageInputPort | None = None,
    ia: IAInputPort | None = None,
    ux: UXInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    brand: BrandInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    planner: ExecutionPlannerPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        design_system=design_system or NullDesignSystemInput(),
        component_intelligence=component_intelligence or NullComponentIntelligenceInput(),
        wireframe=wireframe or NullWireframeInput(),
        creative_director=creative_director or NullCreativeDirectorInput(),
        design_language=design_language or NullDesignLanguageInput(),
        ia=ia or NullIAInput(),
        ux=ux or NullUXInput(),
        psychology=psychology or NullPsychologyInput(),
        brand=brand or NullBrandInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        planner=planner or RuleBasedExecutionPlanner(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the design-orchestrator tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
