"""ComponentIntelligenceInputAdapter — feeds the Phase-15 Component Intelligence into the engine.

Implements :class:`ComponentIntelligenceInputPort` over the Phase-15 facade, translating the
neutral design-system bundle (the included components) into :class:`RawSignal` s (provenance
``COMPONENT_INTELLIGENCE``), so the engine builds component sets for exactly the components the
composition included. The figma-design domain never imports Phase 15 — nor any Figma SDK — so this
adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from component_intelligence.domain.shared.ids import ComponentSpecId
from component_intelligence.interfaces.component_intelligence_facade import (
    ComponentIntelligenceFacade,
)

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext
from figma_design.domain.shared.value_objects import ProvenanceKind

__all__ = ["ComponentIntelligenceInputAdapter"]


class ComponentIntelligenceInputAdapter:
    """Implements :class:`ComponentIntelligenceInputPort` over a Phase-15 composition."""

    def __init__(
        self, facade: ComponentIntelligenceFacade, spec_id: ComponentSpecId
    ) -> None:
        self._facade = facade
        self._spec_id = spec_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.design_system_bundle(self._spec_id)
        ref = str(self._spec_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.COMPONENT_INTELLIGENCE,
                external_ref=f"{ref}:composition",
                claim="The composition fixes which components exist and become component sets.",
                confidence=0.9,
                source_name="Component Intelligence",
                tags=("component-set", "variant", "instance"),
            )
        ]
        for decision in bundle.components:
            component = decision.get("component", "")
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.COMPONENT_INTELLIGENCE,
                    external_ref=f"{ref}:component:{component}",
                    claim=f"Component {component} is included and must have a component set.",
                    confidence=0.85,
                    source_name="Component Intelligence",
                    tags=(component, "component-set", "instance"),
                )
            )
        return signals
