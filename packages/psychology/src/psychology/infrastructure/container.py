"""Composition root — where concrete adapters meet the psychology application.

Assembles the engine (with its pipeline stages) and the facade from injected ports.
Provides a batteries-included in-memory environment — defaulting to the deterministic
rule-based psychologist and null input ports — and helpers to build the engine over any
ports (e.g. the real Phase 8 / Phase 7 / Phase 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

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
from psychology.application.ports.unit_of_work import UnitOfWorkFactory
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
from psychology.infrastructure.inmemory import (
    ReportStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from psychology.interfaces.psychology_facade import PsychologyFacade

__all__ = [
    "PsychologyEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    brand: BrandInputPort,
    business_strategy: BusinessStrategyInputPort,
    knowledge: KnowledgeAdvisorPort,
    research: ResearchInputPort,
    competitor: CompetitorInsightPort,
    reasoning: ReasoningPort,
    synthesis: PsychologySynthesisPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> PsychologyEngine:
    """Assemble a :class:`PsychologyEngine` from its ports."""
    return PsychologyEngine(
        brand=brand,
        business_strategy=business_strategy,
        knowledge=knowledge,
        research=research,
        competitor=competitor,
        reasoning=reasoning,
        synthesis=synthesis,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(
    engine: PsychologyEngine, uow_factory: UnitOfWorkFactory
) -> PsychologyFacade:
    """Wrap an engine in its inbound facade."""
    return PsychologyFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class PsychologyEnvironment:
    """A fully wired engine plus a handle to its in-memory report store."""

    facade: PsychologyFacade
    engine: PsychologyEngine
    storage: ReportStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    brand: BrandInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: PsychologySynthesisPort | None = None,
    clock: Clock | None = None,
) -> PsychologyEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the
    psychologist defaults to the deterministic rule-based implementation.
    """
    storage = ReportStorage()
    uow_factory = make_unit_of_work_factory(storage)
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
    return PsychologyEnvironment(
        facade=facade,
        engine=engine,
        storage=storage,
        unit_of_work_factory=uow_factory,
    )
