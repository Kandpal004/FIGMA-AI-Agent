"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the ten signal ports, the architect, a clock),
wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the in-memory
container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from design_system.application.design_system_engine import DesignSystemEngine
from design_system.application.ports.brand_input import BrandInputPort
from design_system.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_system.application.ports.clock import Clock
from design_system.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from design_system.application.ports.creative_director_input import CreativeDirectorInputPort
from design_system.application.ports.design_language_input import DesignLanguageInputPort
from design_system.application.ports.ia_input import IAInputPort
from design_system.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_system.application.ports.psychology_input import PsychologyInputPort
from design_system.application.ports.token_architect import TokenArchitectPort
from design_system.application.ports.ux_input import UXInputPort
from design_system.application.ports.wireframe_input import WireframeInputPort
from design_system.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullComponentIntelligenceInput,
    NullCreativeDirectorInput,
    NullDesignLanguageInput,
    NullIAInput,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullUXInput,
    NullWireframeInput,
)
from design_system.infrastructure.adapters.rule_based_token_architect import (
    RuleBasedTokenArchitect,
)
from design_system.infrastructure.container import build_engine, build_facade
from design_system.infrastructure.inmemory import SystemClock
from design_system.infrastructure.persistence.models import Base
from design_system.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from design_system.interfaces.design_system_facade import DesignSystemFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: DesignSystemFacade
    engine: DesignSystemEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    design_language: DesignLanguageInputPort | None = None,
    component_intelligence: ComponentIntelligenceInputPort | None = None,
    creative_director: CreativeDirectorInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    brand: BrandInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    ux: UXInputPort | None = None,
    ia: IAInputPort | None = None,
    wireframe: WireframeInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    architect: TokenArchitectPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        design_language=design_language or NullDesignLanguageInput(),
        component_intelligence=component_intelligence or NullComponentIntelligenceInput(),
        creative_director=creative_director or NullCreativeDirectorInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        brand=brand or NullBrandInput(),
        psychology=psychology or NullPsychologyInput(),
        ux=ux or NullUXInput(),
        ia=ia or NullIAInput(),
        wireframe=wireframe or NullWireframeInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        architect=architect or RuleBasedTokenArchitect(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the design-system tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
