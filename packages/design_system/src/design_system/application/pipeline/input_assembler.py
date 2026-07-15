"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (Design Language, Component Intelligence, Creative
Director, business strategy, brand, psychology, UX, IA, wireframe, knowledge) and folds them,
with the brief and project, into a single :class:`DesignSystemInput`. Ports are queried
concurrently; any that returns nothing simply contributes nothing. The Design Language grounds
the token foundation; Component Intelligence grounds which components to spec; the Creative
Director sets the aesthetic bar; UX and psychology ground states, motion, and accessibility.
"""

from __future__ import annotations

import asyncio

from design_system.application.contracts import DesignSystemInput, RawSignal
from design_system.application.ports.brand_input import BrandInputPort
from design_system.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_system.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from design_system.application.ports.creative_director_input import CreativeDirectorInputPort
from design_system.application.ports.design_language_input import DesignLanguageInputPort
from design_system.application.ports.ia_input import IAInputPort
from design_system.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_system.application.ports.psychology_input import PsychologyInputPort
from design_system.application.ports.ux_input import UXInputPort
from design_system.application.ports.wireframe_input import WireframeInputPort
from design_system.application.request import DesignSystemRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the design-system input from the ten signal ports."""

    # The design-system topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "design tokens",
        "three tier token architecture",
        "semantic tokens",
        "theming and dark mode",
        "accessibility WCAG contrast",
        "right to left RTL",
        "component variants and states",
        "atomic design",
        "responsive breakpoints and grid",
        "shopify polaris design system",
        "magento adobe commerce theming",
        "design system anti-patterns",
    )

    async def assemble(
        self,
        request: DesignSystemRequest,
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
    ) -> DesignSystemInput:
        results = await asyncio.gather(
            design_language.gather(request.project),
            component_intelligence.gather(request.project),
            creative_director.gather(request.project),
            business_strategy.gather(request.project),
            brand.gather(request.project),
            psychology.gather(request.project),
            ux.gather(request.project),
            ia.gather(request.project),
            wireframe.gather(request.project),
            knowledge.advise(self._TOPICS, request.project),
        )
        signals: list[RawSignal] = [s for group in results for s in group]
        return DesignSystemInput(
            brief=request.brief, project=request.project, signals=tuple(signals)
        )
