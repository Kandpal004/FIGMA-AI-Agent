"""DesignSystemInputAdapter — feeds the Phase-16 Design System into the engine.

Implements :class:`DesignSystemInputPort` over the Phase-16 Design System facade, translating the
token set and component specs into :class:`RawSignal` s (provenance ``DESIGN_SYSTEM``), so the
orchestrator binds only tokens and variants the design system actually declares. The orchestrator
domain never imports Phase 16, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_system.domain.shared.ids import DesignSystemSpecId
from design_system.interfaces.design_system_facade import DesignSystemFacade

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext
from design_orchestrator.domain.shared.value_objects import ProvenanceKind

__all__ = ["DesignSystemInputAdapter"]


class DesignSystemInputAdapter:
    """Implements :class:`DesignSystemInputPort` over a Phase-16 design-system spec."""

    def __init__(self, facade: DesignSystemFacade, spec_id: DesignSystemSpecId) -> None:
        self._facade = facade
        self._spec_id = spec_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        view = await self._facade.get(self._spec_id)
        ref = str(self._spec_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.DESIGN_SYSTEM,
                external_ref=f"{ref}:tokens",
                claim="Every section must bind Design System tokens; no hard-coded values.",
                confidence=0.9,
                source_name="Design System",
                tags=("token", "binding", "theme", "surface", "spacing", "typography"),
            )
        ]
        for spec in view.components:
            component = spec.get("component", "")
            variants = [v.get("name", "") for v in spec.get("variants", ())]
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.DESIGN_SYSTEM,
                    external_ref=f"{ref}:component:{component}",
                    claim=f"Component {component} offers variants {variants} and its declared "
                    "token references.",
                    confidence=0.85,
                    source_name="Design System",
                    tags=(component, "variant", "token", "component"),
                )
            )
        return signals
