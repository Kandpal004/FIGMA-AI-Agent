"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (Design System, Component Intelligence, Wireframe,
Creative Director, Design Language, IA, UX, psychology, brand, business strategy, knowledge) and
folds them, with the brief, project, and source refs, into a single :class:`OrchestrationInput`.
Ports are queried concurrently; any that returns nothing simply contributes nothing. The
Wireframe drives section order; Component Intelligence fixes which components exist; the Design
System fixes the tokens and variants; the Creative Director sets the review gates.
"""

from __future__ import annotations

import asyncio

from design_orchestrator.application.contracts import OrchestrationInput, RawSignal
from design_orchestrator.application.ports.brand_input import BrandInputPort
from design_orchestrator.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_orchestrator.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from design_orchestrator.application.ports.creative_director_input import CreativeDirectorInputPort
from design_orchestrator.application.ports.design_language_input import DesignLanguageInputPort
from design_orchestrator.application.ports.design_system_input import DesignSystemInputPort
from design_orchestrator.application.ports.ia_input import IAInputPort
from design_orchestrator.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_orchestrator.application.ports.psychology_input import PsychologyInputPort
from design_orchestrator.application.ports.ux_input import UXInputPort
from design_orchestrator.application.ports.wireframe_input import WireframeInputPort
from design_orchestrator.application.request import OrchestrationRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the orchestration input from the eleven signal ports."""

    # The orchestration topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "page composition and section ordering",
        "above the fold priority",
        "conversion sequencing",
        "trust placement",
        "progressive disclosure",
        "design review checkpoints",
        "responsive section strategy",
        "accessibility gating",
        "performance budget sequencing",
        "design execution planning",
    )

    async def assemble(
        self,
        request: OrchestrationRequest,
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
    ) -> OrchestrationInput:
        results = await asyncio.gather(
            design_system.gather(request.project),
            component_intelligence.gather(request.project),
            wireframe.gather(request.project),
            creative_director.gather(request.project),
            design_language.gather(request.project),
            ia.gather(request.project),
            ux.gather(request.project),
            psychology.gather(request.project),
            brand.gather(request.project),
            business_strategy.gather(request.project),
            knowledge.advise(self._TOPICS, request.project),
        )
        signals: list[RawSignal] = [s for group in results for s in group]
        return OrchestrationInput(
            brief=request.brief,
            project=request.project,
            source_refs=request.source_refs,
            signals=tuple(signals),
        )
