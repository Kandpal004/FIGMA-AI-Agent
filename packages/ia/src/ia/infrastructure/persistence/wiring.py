"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the eight signal ports, the architect, a
clock), wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the
in-memory container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from ia.application.ia_engine import IAEngine
from ia.application.ports.brand_input import BrandInputPort
from ia.application.ports.business_strategy_input import BusinessStrategyInputPort
from ia.application.ports.clock import Clock
from ia.application.ports.competitor_insight import CompetitorInsightPort
from ia.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from ia.application.ports.psychology_input import PsychologyInputPort
from ia.application.ports.reasoning import ReasoningPort
from ia.application.ports.research_input import ResearchInputPort
from ia.application.ports.synthesis import IASynthesisPort
from ia.application.ports.ux_input import UXInputPort
from ia.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullReasoning,
    NullResearchInput,
    NullUXInput,
)
from ia.infrastructure.adapters.rule_based_ia_architect import RuleBasedIAArchitect
from ia.infrastructure.container import build_engine, build_facade
from ia.infrastructure.inmemory import SystemClock
from ia.infrastructure.persistence.models import Base
from ia.infrastructure.persistence.unit_of_work import make_sqlalchemy_unit_of_work_factory
from ia.interfaces.ia_facade import IAFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: IAFacade
    engine: IAEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    ux: UXInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    brand: BrandInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: IASynthesisPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        ux=ux or NullUXInput(),
        psychology=psychology or NullPsychologyInput(),
        brand=brand or NullBrandInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedIAArchitect(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the IA tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
