"""WireframeInputAdapter — feeds the Phase-12 Wireframe plan (the primary driver) into the engine.

Implements :class:`WireframeInputPort` over the Phase-12 wireframe facade: it pulls the plan's
neutral Figma plan bundle and translates its pages, sections, and components into
:class:`RawSignal` s (provenance ``WIREFRAME``) tagged so the component brain can see which
components the storefront's structure demands. This is the primary driver of which components
exist. The component-intelligence domain never imports Phase 12, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from wireframe.domain.shared.ids import WireframePlanId
from wireframe.interfaces.wireframe_facade import WireframeFacade

from component_intelligence.application.contracts import RawSignal
from component_intelligence.domain.context.context import ProjectContext
from component_intelligence.domain.shared.value_objects import ProvenanceKind

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
                provenance=ProvenanceKind.WIREFRAME, external_ref=f"{ref}:plan",
                claim="The wireframe plan defines the sections and components each page needs.",
                confidence=0.9, source_name="Wireframe Plan",
                tags=("component", "section", "structure", "buy", "cart", "conversion"),
            ),
        ]
        for page in bundle.pages:
            for section in page.get("sections", ()):
                stype = section.get("type", "")
                comps = [c.get("component", "") for c in section.get("required_components", ())]
                tags = [page["page_type"], stype, "component", "section", "structure"]
                tags.extend(comps)
                signals.append(
                    RawSignal(
                        provenance=ProvenanceKind.WIREFRAME,
                        external_ref=f"{ref}:section:{page['page_type']}:{stype}",
                        claim=f"{stype} section on {page['page_type']} needs its components.",
                        confidence=0.85, source_name="Wireframe Plan",
                        tags=tuple(t for t in tags if t),
                    )
                )
        return signals
