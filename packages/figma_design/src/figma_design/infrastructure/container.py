"""Composition root — where concrete adapters meet the figma-design application.

Assembles the engine (with its pipeline stages) and the facade from injected ports. Provides a
batteries-included in-memory environment — defaulting to the deterministic rule-based composer and
null input ports — and helpers to build the engine over any ports (e.g. the real Phase
17 / 16 / 15 / 14 / 13 / 3 adapters). No Figma SDK, MCP client, or HTTP library is imported here.
"""

from __future__ import annotations

from dataclasses import dataclass

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
from figma_design.application.ports.unit_of_work import UnitOfWorkFactory
from figma_design.infrastructure.adapters.inmemory_inputs import (
    NullComponentIntelligenceInput,
    NullCreativeDirectorInput,
    NullDesignLanguageInput,
    NullDesignOrchestratorInput,
    NullDesignSystemInput,
    NullKnowledgeAdvisor,
)
from figma_design.infrastructure.adapters.rule_based_figma_composer import RuleBasedFigmaComposer
from figma_design.infrastructure.inmemory import (
    ModelStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from figma_design.interfaces.figma_design_facade import FigmaDesignFacade

__all__ = [
    "FigmaDesignEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    design_orchestrator: DesignOrchestratorInputPort,
    design_system: DesignSystemInputPort,
    component_intelligence: ComponentIntelligenceInputPort,
    design_language: DesignLanguageInputPort,
    creative_director: CreativeDirectorInputPort,
    knowledge: KnowledgeAdvisorPort,
    composer: FigmaComposerPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> FigmaDesignEngine:
    """Assemble a :class:`FigmaDesignEngine` from its ports."""
    return FigmaDesignEngine(
        design_orchestrator=design_orchestrator,
        design_system=design_system,
        component_intelligence=component_intelligence,
        design_language=design_language,
        creative_director=creative_director,
        knowledge=knowledge,
        composer=composer,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(
    engine: FigmaDesignEngine, uow_factory: UnitOfWorkFactory
) -> FigmaDesignFacade:
    """Wrap an engine in its inbound facade."""
    return FigmaDesignFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class FigmaDesignEnvironment:
    """A fully wired engine plus a handle to its in-memory model store."""

    facade: FigmaDesignFacade
    engine: FigmaDesignEngine
    storage: ModelStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    design_orchestrator: DesignOrchestratorInputPort | None = None,
    design_system: DesignSystemInputPort | None = None,
    component_intelligence: ComponentIntelligenceInputPort | None = None,
    design_language: DesignLanguageInputPort | None = None,
    creative_director: CreativeDirectorInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    composer: FigmaComposerPort | None = None,
    clock: Clock | None = None,
) -> FigmaDesignEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the composer
    defaults to the deterministic rule-based implementation.
    """
    storage = ModelStorage()
    uow_factory = make_unit_of_work_factory(storage)
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
    return FigmaDesignEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
