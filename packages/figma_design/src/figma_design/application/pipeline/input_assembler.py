"""Stage 1 — Input Assembly.

Gathers neutral signals from every input port (Design Orchestrator, Design System, Component
Intelligence, Design Language, Creative Director, Knowledge) and folds them, with the brief,
project, and source refs, into a single :class:`FigmaInput`. Ports are queried concurrently; any
that returns nothing simply contributes nothing. The Design Orchestrator drives the pages and
sections; the Design System fixes the variables and styles; Component Intelligence fixes the
component sets; the Creative Director sets the quality bar and handoff expectations.
"""

from __future__ import annotations

import asyncio

from figma_design.application.contracts import FigmaInput, RawSignal
from figma_design.application.ports.component_intelligence_input import (
    ComponentIntelligenceInputPort,
)
from figma_design.application.ports.creative_director_input import CreativeDirectorInputPort
from figma_design.application.ports.design_language_input import DesignLanguageInputPort
from figma_design.application.ports.design_orchestrator_input import DesignOrchestratorInputPort
from figma_design.application.ports.design_system_input import DesignSystemInputPort
from figma_design.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from figma_design.application.request import FigmaDesignRequest

__all__ = ["InputAssembler"]


class InputAssembler:
    """Assembles the Figma input from the six signal ports."""

    # The Figma file-craft topics the knowledge advisor is asked to ground.
    _TOPICS = (
        "figma file organization",
        "variable collections and modes",
        "auto layout and nested auto layout",
        "component sets and variants",
        "published styles and libraries",
        "responsive frames desktop tablet mobile",
        "dev mode and developer handoff",
        "design tokens as variables",
        "component properties",
        "professional figma structure",
    )

    async def assemble(
        self,
        request: FigmaDesignRequest,
        *,
        design_orchestrator: DesignOrchestratorInputPort,
        design_system: DesignSystemInputPort,
        component_intelligence: ComponentIntelligenceInputPort,
        design_language: DesignLanguageInputPort,
        creative_director: CreativeDirectorInputPort,
        knowledge: KnowledgeAdvisorPort,
    ) -> FigmaInput:
        results = await asyncio.gather(
            design_orchestrator.gather(request.project),
            design_system.gather(request.project),
            component_intelligence.gather(request.project),
            design_language.gather(request.project),
            creative_director.gather(request.project),
            knowledge.advise(self._TOPICS, request.project),
        )
        signals: list[RawSignal] = [s for group in results for s in group]
        return FigmaInput(
            brief=request.brief,
            project=request.project,
            source_refs=request.source_refs,
            signals=tuple(signals),
        )
