"""Composition root — where concrete adapters meet the design-system application.

Assembles the engine (with its pipeline stages) and the facade from injected ports. Provides a
batteries-included in-memory environment — defaulting to the deterministic rule-based architect
and null input ports — and helpers to build the engine over any ports (e.g. the real Phase
15 / 14 / 13 / 12 / 11 / 10 / 9 / 8 / 7 / 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

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
from design_system.application.ports.unit_of_work import UnitOfWorkFactory
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
from design_system.infrastructure.inmemory import (
    SpecificationStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from design_system.interfaces.design_system_facade import DesignSystemFacade

__all__ = [
    "DesignSystemEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    design_language: DesignLanguageInputPort,
    component_intelligence: ComponentIntelligenceInputPort,
    creative_director: CreativeDirectorInputPort,
    business_strategy: BusinessStrategyInputPort,
    brand: BrandInputPort,
    psychology: PsychologyInputPort,
    ux: UXInputPort,
    ia: IAInputPort,
    wireframe: WireframeInputPort,
    knowledge: KnowledgeAdvisorPort,
    architect: TokenArchitectPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> DesignSystemEngine:
    """Assemble a :class:`DesignSystemEngine` from its ports."""
    return DesignSystemEngine(
        design_language=design_language,
        component_intelligence=component_intelligence,
        creative_director=creative_director,
        business_strategy=business_strategy,
        brand=brand,
        psychology=psychology,
        ux=ux,
        ia=ia,
        wireframe=wireframe,
        knowledge=knowledge,
        architect=architect,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(
    engine: DesignSystemEngine, uow_factory: UnitOfWorkFactory
) -> DesignSystemFacade:
    """Wrap an engine in its inbound facade."""
    return DesignSystemFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class DesignSystemEnvironment:
    """A fully wired engine plus a handle to its in-memory specification store."""

    facade: DesignSystemFacade
    engine: DesignSystemEngine
    storage: SpecificationStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
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
) -> DesignSystemEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the architect
    defaults to the deterministic rule-based implementation.
    """
    storage = SpecificationStorage()
    uow_factory = make_unit_of_work_factory(storage)
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
    return DesignSystemEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
