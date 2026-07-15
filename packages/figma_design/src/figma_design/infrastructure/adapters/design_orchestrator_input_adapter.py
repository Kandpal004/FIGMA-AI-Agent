"""DesignOrchestratorInputAdapter — feeds the Phase-17 execution plan into the engine.

Implements :class:`DesignOrchestratorInputPort` over the Phase-17 Design Orchestrator facade,
translating the design-execution plan (the ordered pages and sections, the token/variant bindings)
into :class:`RawSignal` s (provenance ``DESIGN_ORCHESTRATOR``), the primary driver of the Figma
file. The figma-design domain never imports Phase 17 — nor any Figma SDK — so this adapter is the
seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_orchestrator.domain.shared.ids import DesignExecutionPlanId
from design_orchestrator.interfaces.design_orchestrator_facade import DesignOrchestratorFacade

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext
from figma_design.domain.shared.value_objects import ProvenanceKind

__all__ = ["DesignOrchestratorInputAdapter"]


class DesignOrchestratorInputAdapter:
    """Implements :class:`DesignOrchestratorInputPort` over a Phase-17 execution plan."""

    def __init__(
        self, facade: DesignOrchestratorFacade, plan_id: DesignExecutionPlanId
    ) -> None:
        self._facade = facade
        self._plan_id = plan_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.execution_bundle(self._plan_id)
        ref = str(self._plan_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.DESIGN_ORCHESTRATOR,
                external_ref=f"{ref}:plan",
                claim="The execution plan defines the pages, the section order, and the token and "
                "variant bindings the Figma file must realise.",
                confidence=0.9,
                source_name="Design Orchestrator",
                tags=("page", "section", "order", "auto-layout", "instance"),
            )
        ]
        for page in bundle.pages:
            page_type = page.get("page_type", "")
            sections = page.get("sections", ())
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.DESIGN_ORCHESTRATOR,
                    external_ref=f"{ref}:page:{page_type}",
                    claim=f"{page_type} page: {len(sections)} ordered sections to lay out.",
                    confidence=0.85,
                    source_name="Design Orchestrator",
                    tags=(page_type, "page", "section", "frame"),
                )
            )
        return signals
