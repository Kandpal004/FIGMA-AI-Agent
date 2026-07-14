"""UXInputAdapter — feeds Phase-10 UX Strategy into the information architecture.

Implements :class:`UXInputPort` over the Phase-10 UX facade: it pulls a UX strategy's neutral
design brief bundle and translates its primary user goal, per-page objectives + CTAs +
priorities, navigation, and friction points into :class:`RawSignal` s (provenance
``UX_STRATEGY``). The adapter is bound to a resolved UX report; the IA domain never imports
Phase 10, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from ux.domain.shared.ids import UXReportId
from ux.interfaces.ux_facade import UXFacade

from ia.application.contracts import RawSignal
from ia.domain.context.context import ProjectContext
from ia.domain.shared.value_objects import ProvenanceKind

__all__ = ["UXInputAdapter"]


class UXInputAdapter:
    """Implements :class:`UXInputPort` over a Phase-10 UX report."""

    def __init__(self, facade: UXFacade, report_id: UXReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.design_brief_bundle(self._report_id)
        ref = str(self._report_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.UX_STRATEGY, external_ref=f"{ref}:goal",
                claim=bundle.primary_user_goal, confidence=0.9, source_name="UX Strategy",
                tags=("goal", "user", "conversion"),
            ),
            RawSignal(
                provenance=ProvenanceKind.UX_STRATEGY, external_ref=f"{ref}:navigation",
                claim=f"Navigation pattern: {bundle.navigation.get('pattern', '')}.", confidence=0.85,
                source_name="UX Strategy", tags=("navigation", "nav", "convention", "menu"),
            ),
        ]
        for page in bundle.pages:
            cta = page.get("primary_cta") or ""
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.UX_STRATEGY, external_ref=f"{ref}:page:{page['page']}",
                    claim=f"{page['page']} page: {page.get('objective', '')} (primary CTA: {cta}).",
                    confidence=0.85, source_name="UX Strategy",
                    tags=(page["page"], "page", "cta", "conversion", "trust"),
                )
            )
        for friction in bundle.friction_points:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.UX_STRATEGY,
                    external_ref=f"{ref}:friction:{friction.get('phase', '')}:{friction.get('kind', '')}",
                    claim=f"Friction ({friction.get('kind', '')}): {friction.get('location', '')}.",
                    confidence=0.8, source_name="UX Strategy",
                    tags=(friction.get("kind", ""), "friction", friction.get("phase", "")),
                )
            )
        return signals
