"""DesignSystemInputAdapter — feeds the Phase-16 Design System into the engine.

Implements :class:`DesignSystemInputPort` over the Phase-16 Design System facade, translating the
token set and component specs into :class:`RawSignal` s (provenance ``DESIGN_SYSTEM``), so the
Figma variables, styles, and component sets are grounded in the design system. The figma-design
domain never imports Phase 16 — nor any Figma SDK — so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_system.domain.shared.ids import DesignSystemSpecId
from design_system.interfaces.design_system_facade import DesignSystemFacade

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext
from figma_design.domain.shared.value_objects import ProvenanceKind

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
                claim="The token set becomes the Figma variable collections (theme light/dark, "
                "primitives, device) and the published styles.",
                confidence=0.9,
                source_name="Design System",
                tags=("variable", "collection", "mode", "style", "token"),
            )
        ]
        for spec in view.components:
            component = spec.get("component", "")
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.DESIGN_SYSTEM,
                    external_ref=f"{ref}:component:{component}",
                    claim=f"Component {component} becomes a Figma component set with its variants.",
                    confidence=0.85,
                    source_name="Design System",
                    tags=(component, "component-set", "variant"),
                )
            )
        return signals
