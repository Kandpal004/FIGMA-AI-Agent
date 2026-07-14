"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the six signal ports, the psychologist, a
clock), wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the
in-memory container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from psychology.application.ports.brand_input import BrandInputPort
from psychology.application.ports.business_strategy_input import (
    BusinessStrategyInputPort,
)
from psychology.application.ports.clock import Clock
from psychology.application.ports.competitor_insight import CompetitorInsightPort
from psychology.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from psychology.application.ports.reasoning import ReasoningPort
from psychology.application.ports.research_input import ResearchInputPort
from psychology.application.ports.synthesis import PsychologySynthesisPort
from psychology.application.psychology_engine import PsychologyEngine
from psychology.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullKnowledgeAdvisor,
    NullReasoning,
    NullResearchInput,
)
from psychology.infrastructure.adapters.rule_based_psychologist import (
    RuleBasedPsychologist,
)
from psychology.infrastructure.container import build_engine, build_facade
from psychology.infrastructure.inmemory import SystemClock
from psychology.infrastructure.persistence.models import Base
from psychology.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from psychology.interfaces.psychology_facade import PsychologyFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: PsychologyFacade
    engine: PsychologyEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    brand: BrandInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: PsychologySynthesisPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        brand=brand or NullBrandInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedPsychologist(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the psychology tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
