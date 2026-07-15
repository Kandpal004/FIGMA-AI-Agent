"""BrandInputAdapter — feeds the Phase-8 Brand Strategy into the engine.

Implements :class:`BrandInputPort` over the Phase-8 brand facade, translating the guidelines
bundle into :class:`RawSignal` s (provenance ``BRAND_STRATEGY``), so the colour and type
primitives are grounded in the brand. The design-system domain never imports Phase 8, so this
adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from brand.domain.shared.ids import BrandReportId
from brand.interfaces.brand_facade import BrandFacade

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext
from design_system.domain.shared.value_objects import ProvenanceKind

__all__ = ["BrandInputAdapter"]


class BrandInputAdapter:
    """Implements :class:`BrandInputPort` over a Phase-8 brand report."""

    def __init__(self, facade: BrandFacade, report_id: BrandReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.guidelines_bundle(self._report_id)
        ref = str(self._report_id)
        return [
            RawSignal(
                provenance=ProvenanceKind.BRAND_STRATEGY,
                external_ref=f"{ref}:tone",
                claim=f"Brand tone {bundle.tone} shapes the colour palette and type primitives.",
                confidence=0.8,
                source_name="Brand Strategy",
                tags=(bundle.archetype, bundle.tone, "brand", "color", "typography"),
            )
        ]
