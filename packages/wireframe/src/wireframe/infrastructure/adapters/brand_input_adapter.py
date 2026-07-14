"""BrandInputAdapter — feeds Phase-8 Brand Strategy into the wireframe plan.

Implements :class:`BrandInputPort` over the Phase-8 brand facade: it pulls a brand's neutral
guidelines bundle and translates its archetype, tone, and positioning into :class:`RawSignal`
s (provenance ``BRAND_STRATEGY``), so content and trust emphasis carry the brand. The
wireframe domain never imports Phase 8, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from brand.domain.shared.ids import BrandReportId
from brand.interfaces.brand_facade import BrandFacade

from wireframe.application.contracts import RawSignal
from wireframe.domain.context.context import ProjectContext
from wireframe.domain.shared.value_objects import ProvenanceKind

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
                provenance=ProvenanceKind.BRAND_STRATEGY, external_ref=f"{ref}:positioning",
                claim=bundle.positioning_statement, confidence=0.85, source_name="Brand Strategy",
                tags=(bundle.archetype, "positioning", "brand", "tone"),
            ),
            RawSignal(
                provenance=ProvenanceKind.BRAND_STRATEGY, external_ref=f"{ref}:tone",
                claim=f"Brand tone: {bundle.tone} (archetype {bundle.archetype}).",
                confidence=0.8, source_name="Brand Strategy",
                tags=(bundle.tone, "tone", "brand", "voice"),
            ),
        ]
