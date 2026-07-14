"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the nine signal ports, the planner, a clock),
wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the in-memory
container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from wireframe.application.ports.brand_input import BrandInputPort
from wireframe.application.ports.business_strategy_input import BusinessStrategyInputPort
from wireframe.application.ports.clock import Clock
from wireframe.application.ports.competitor_insight import CompetitorInsightPort
from wireframe.application.ports.ia_input import IAInputPort
from wireframe.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from wireframe.application.ports.psychology_input import PsychologyInputPort
from wireframe.application.ports.reasoning import ReasoningPort
from wireframe.application.ports.research_input import ResearchInputPort
from wireframe.application.ports.synthesis import WireframeSynthesisPort
from wireframe.application.ports.ux_input import UXInputPort
from wireframe.application.wireframe_engine import WireframeEngine
from wireframe.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullIAInput,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullReasoning,
    NullResearchInput,
    NullUXInput,
)
from wireframe.infrastructure.adapters.rule_based_wireframe_planner import (
    RuleBasedWireframePlanner,
)
from wireframe.infrastructure.container import build_engine, build_facade
from wireframe.infrastructure.inmemory import SystemClock
from wireframe.infrastructure.persistence.models import Base
from wireframe.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from wireframe.interfaces.wireframe_facade import WireframeFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: WireframeFacade
    engine: WireframeEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    ia: IAInputPort | None = None,
    ux: UXInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    brand: BrandInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: WireframeSynthesisPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        ia=ia or NullIAInput(),
        ux=ux or NullUXInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        brand=brand or NullBrandInput(),
        psychology=psychology or NullPsychologyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedWireframePlanner(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the wireframe tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
