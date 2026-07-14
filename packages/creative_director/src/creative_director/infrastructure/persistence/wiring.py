"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the ten signal ports, the panel, a clock),
wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the in-memory
container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from creative_director.application.creative_director_engine import CreativeDirectorEngine
from creative_director.application.ports.brand_input import BrandInputPort
from creative_director.application.ports.business_strategy_input import BusinessStrategyInputPort
from creative_director.application.ports.clock import Clock
from creative_director.application.ports.competitor_insight import CompetitorInsightPort
from creative_director.application.ports.ia_input import IAInputPort
from creative_director.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from creative_director.application.ports.psychology_input import PsychologyInputPort
from creative_director.application.ports.reasoning import ReasoningPort
from creative_director.application.ports.research_input import ResearchInputPort
from creative_director.application.ports.review_panel import ReviewPanelPort
from creative_director.application.ports.ux_input import UXInputPort
from creative_director.application.ports.wireframe_input import WireframeInputPort
from creative_director.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullIAInput,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullReasoning,
    NullResearchInput,
    NullUXInput,
    NullWireframeInput,
)
from creative_director.infrastructure.adapters.rule_based_review_panel import (
    RuleBasedReviewPanel,
)
from creative_director.infrastructure.container import build_engine, build_facade
from creative_director.infrastructure.inmemory import SystemClock
from creative_director.infrastructure.persistence.models import Base
from creative_director.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from creative_director.interfaces.creative_director_facade import CreativeDirectorFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: CreativeDirectorFacade
    engine: CreativeDirectorEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    wireframe: WireframeInputPort | None = None,
    ia: IAInputPort | None = None,
    ux: UXInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    brand: BrandInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    panel: ReviewPanelPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    the_clock = clock or SystemClock()
    engine = build_engine(
        wireframe=wireframe or NullWireframeInput(),
        ia=ia or NullIAInput(),
        ux=ux or NullUXInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        brand=brand or NullBrandInput(),
        psychology=psychology or NullPsychologyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        panel=panel or RuleBasedReviewPanel(),
        unit_of_work_factory=uow_factory,
        clock=the_clock,
    )
    facade = build_facade(engine, uow_factory, the_clock)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the Creative Director tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
