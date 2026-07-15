"""WireframeInputAdapter — feeds the Phase-12 Wireframe plan into the engine.

Implements :class:`WireframeInputPort` over the Phase-12 wireframe facade: it pulls the plan's
neutral Figma plan bundle and translates its pages and sections into :class:`RawSignal` s
(provenance ``WIREFRAME``), so the spacing grid, breakpoints, and layout tokens are grounded in
the intended structure. The design-system domain never imports Phase 12, so this adapter is the
seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from wireframe.domain.shared.ids import WireframePlanId
from wireframe.interfaces.wireframe_facade import WireframeFacade

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext
from design_system.domain.shared.value_objects import ProvenanceKind

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
                external_ref=f"{ref}:grid",
                claim="The wireframe plan defines the responsive grid, breakpoints, and spacing "
                "rhythm the tokens must encode.",
                confidence=0.9,
                source_name="Wireframe Plan",
                tags=("grid", "breakpoint", "spacing", "container", "layout"),
            )
        ]
        for page in bundle.pages:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.WIREFRAME,
                    external_ref=f"{ref}:page:{page['page_type']}",
                    claim=f"{page['page_type']} layout defines its spacing and grid needs.",
                    confidence=0.82,
                    source_name="Wireframe Plan",
                    tags=(page["page_type"], "grid", "spacing", "layout"),
                )
            )
        return signals
