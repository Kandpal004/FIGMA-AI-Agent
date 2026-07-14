"""BrandInputAdapter — feeds Phase-8 Brand Strategy into the psychology model.

Implements :class:`BrandInputPort` over the Phase-8 brand facade: it pulls a brand's
neutral guidelines bundle and translates its category, archetype, tone, positioning, and
validation rules into :class:`RawSignal` s (provenance ``BRAND_STRATEGY``). The adapter is
bound to a resolved brand report; the psychology domain never imports Phase 8, so this
adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from brand.domain.shared.ids import BrandReportId
from brand.interfaces.brand_facade import BrandFacade

from psychology.application.contracts import RawSignal
from psychology.domain.context.context import ProjectContext
from psychology.domain.shared.value_objects import ProvenanceKind

__all__ = ["BrandInputAdapter"]


class BrandInputAdapter:
    """Implements :class:`BrandInputPort` over a Phase-8 brand report."""

    def __init__(self, facade: BrandFacade, report_id: BrandReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.guidelines_bundle(self._report_id)
        ref = str(self._report_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.BRAND_STRATEGY, external_ref=f"{ref}:positioning",
                claim=bundle.positioning_statement, confidence=0.9, source_name="Brand Strategy",
                tags=(bundle.primary_category, "positioning", "brand"),
            ),
            RawSignal(
                provenance=ProvenanceKind.BRAND_STRATEGY, external_ref=f"{ref}:archetype",
                claim=f"The brand embodies the {bundle.archetype} archetype.", confidence=0.85,
                source_name="Brand Strategy", tags=(bundle.archetype, "archetype", "brand", "emotion"),
            ),
            RawSignal(
                provenance=ProvenanceKind.BRAND_STRATEGY, external_ref=f"{ref}:tone",
                claim=f"The brand voice is {bundle.tone}.", confidence=0.8,
                source_name="Brand Strategy", tags=(bundle.tone, "tone", "voice"),
            ),
        ]
        for rule in bundle.validation_rules:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.BRAND_STRATEGY, external_ref=rule.id,
                    claim=rule.assertion, confidence=0.8, source_name="Brand Strategy",
                    tags=(rule.subject, "brand", "rule"),
                )
            )
        return signals
