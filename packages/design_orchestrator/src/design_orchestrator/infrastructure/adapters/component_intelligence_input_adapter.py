"""ComponentIntelligenceInputAdapter — feeds the Phase-15 Component Intelligence into the engine.

Implements :class:`ComponentIntelligenceInputPort` over the Phase-15 facade, translating the
neutral design-system bundle (the included components and their placement) into
:class:`RawSignal` s (provenance ``COMPONENT_INTELLIGENCE``), so the orchestrator only places
components the composition included. The orchestrator domain never imports Phase 15, so this
adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from component_intelligence.domain.shared.ids import ComponentSpecId
from component_intelligence.interfaces.component_intelligence_facade import (
    ComponentIntelligenceFacade,
)

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext
from design_orchestrator.domain.shared.value_objects import ProvenanceKind

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
                claim="The component composition fixes which components exist and on which page.",
                confidence=0.9,
                source_name="Component Intelligence",
                tags=("component", "placement", "composition", "order"),
            )
        ]
        for decision in bundle.components:
            component = decision.get("component", "")
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.COMPONENT_INTELLIGENCE,
                    external_ref=f"{ref}:component:{component}",
                    claim=f"Component {component} is included and must be placed per its "
                    "page affinity.",
                    confidence=0.85,
                    source_name="Component Intelligence",
                    tags=(component, "component", "placement", "order"),
                )
            )
        return signals
