"""WireframeInputAdapter — feeds the Phase-12 Wireframe plan (the primary driver) into the engine.

Implements :class:`WireframeInputPort` over the Phase-12 wireframe facade: it pulls the plan's
neutral Figma plan bundle and translates its pages and sections into :class:`RawSignal` s
(provenance ``WIREFRAME``), the primary driver of page and section ordering. The orchestrator
domain never imports Phase 12, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from wireframe.domain.shared.ids import WireframePlanId
from wireframe.interfaces.wireframe_facade import WireframeFacade

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext
from design_orchestrator.domain.shared.value_objects import ProvenanceKind

__all__ = ["WireframeInputAdapter"]


class WireframeInputAdapter:
    """Implements :class:`WireframeInputPort` over a Phase-12 wireframe plan."""

    def __init__(self, facade: WireframeFacade, plan_id: WireframePlanId) -> None:
        self._facade = facade
        self._plan_id = plan_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.figma_plan_bundle(self._plan_id)
        ref = str(self._plan_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.WIREFRAME,
                external_ref=f"{ref}:order",
                claim="The wireframe plan defines the page set and the section order each needs.",
                confidence=0.9,
                source_name="Wireframe Plan",
                tags=("order", "section", "structure", "page", "sequence"),
            )
        ]
        for page in bundle.pages:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.WIREFRAME,
                    external_ref=f"{ref}:page:{page['page_type']}",
                    claim=f"{page['page_type']} defines its section order.",
                    confidence=0.85,
                    source_name="Wireframe Plan",
                    tags=(page["page_type"], "order", "section", "structure"),
                )
            )
        return signals
