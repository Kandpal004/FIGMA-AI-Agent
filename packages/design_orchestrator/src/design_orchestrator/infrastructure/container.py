"""Composition root — where concrete adapters meet the design-orchestrator application.

Assembles the engine (with its pipeline stages) and the facade from injected ports. Provides a
batteries-included in-memory environment — defaulting to the deterministic rule-based planner and
null input ports — and helpers to build the engine over any ports (e.g. the real Phase
16 / 15 / 14 / 13 / 12 / 11 / 10 / 9 / 8 / 7 / 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

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
from design_orchestrator.application.ports.unit_of_work import UnitOfWorkFactory
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
from design_orchestrator.infrastructure.inmemory import (
    PlanStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from design_orchestrator.interfaces.design_orchestrator_facade import DesignOrchestratorFacade

__all__ = [
    "DesignOrchestratorEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    design_system: DesignSystemInputPort,
    component_intelligence: ComponentIntelligenceInputPort,
    wireframe: WireframeInputPort,
    creative_director: CreativeDirectorInputPort,
    design_language: DesignLanguageInputPort,
    ia: IAInputPort,
    ux: UXInputPort,
    psychology: PsychologyInputPort,
    brand: BrandInputPort,
    business_strategy: BusinessStrategyInputPort,
    knowledge: KnowledgeAdvisorPort,
    planner: ExecutionPlannerPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> DesignOrchestratorEngine:
    """Assemble a :class:`DesignOrchestratorEngine` from its ports."""
    return DesignOrchestratorEngine(
        design_system=design_system,
        component_intelligence=component_intelligence,
        wireframe=wireframe,
        creative_director=creative_director,
        design_language=design_language,
        ia=ia,
        ux=ux,
        psychology=psychology,
        brand=brand,
        business_strategy=business_strategy,
        knowledge=knowledge,
        planner=planner,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(
    engine: DesignOrchestratorEngine, uow_factory: UnitOfWorkFactory
) -> DesignOrchestratorFacade:
    """Wrap an engine in its inbound facade."""
    return DesignOrchestratorFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class DesignOrchestratorEnvironment:
    """A fully wired engine plus a handle to its in-memory plan store."""

    facade: DesignOrchestratorFacade
    engine: DesignOrchestratorEngine
    storage: PlanStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
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
) -> DesignOrchestratorEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the planner
    defaults to the deterministic rule-based implementation.
    """
    storage = PlanStorage()
    uow_factory = make_unit_of_work_factory(storage)
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
    return DesignOrchestratorEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
