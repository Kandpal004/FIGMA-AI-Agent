"""ComponentIntelligenceInputAdapter — feeds the Phase-15 Component Intelligence into the engine.

Implements :class:`ComponentIntelligenceInputPort` over the Phase-15 Component Intelligence
facade. It consumes the *neutral design-system bundle* that Phase 15 produces expressly for this
phase and translates each included component (its atomic level, variants, states, and token
references) into :class:`RawSignal` s (provenance ``COMPONENT_INTELLIGENCE``), so the design
system specs exactly the components the composition calls for. The design-system domain never
imports Phase 15, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from component_intelligence.domain.shared.ids import ComponentSpecId
from component_intelligence.interfaces.component_intelligence_facade import (
    ComponentIntelligenceFacade,
)

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext
from design_system.domain.shared.value_objects import ProvenanceKind

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
                claim="The component composition defines which components the design system "
                "must fully specify (variants, states, tokens, platform mappings).",
                confidence=0.9,
                source_name="Component Intelligence",
                tags=("component", "variant", "state", "token", "atomic"),
            )
        ]
        for decision in bundle.components:
            component = decision.get("component", "")
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.COMPONENT_INTELLIGENCE,
                    external_ref=f"{ref}:component:{component}",
                    claim=f"Component {component} ({decision.get('atomic_level', '')}) must be "
                    "specified with its variants, states, and token references.",
                    confidence=0.85,
                    source_name="Component Intelligence",
                    tags=(component, decision.get("atomic_level", ""), "component", "variant",
                          "state", "token"),
                )
            )
        return signals
