"""UXInputAdapter — feeds the Phase-10 UX Strategy into the review.

Implements :class:`UXInputPort` over the Phase-10 UX facade: it pulls the UX strategy's
neutral design brief bundle and translates its primary goal, per-page objectives and CTAs, and
navigation into :class:`RawSignal` s (provenance ``UX_STRATEGY``), so the UX-quality and
conversion reviews are grounded. The creative-director domain never imports Phase 10, so this
adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from ux.domain.shared.ids import UXReportId
from ux.interfaces.ux_facade import UXFacade

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext
from creative_director.domain.shared.value_objects import ProvenanceKind

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
                tags=("ux", "goal", "user", "flow", "conversion"),
            ),
            RawSignal(
                provenance=ProvenanceKind.UX_STRATEGY, external_ref=f"{ref}:navigation",
                claim=f"Navigation pattern: {bundle.navigation.get('pattern', '')}.",
                confidence=0.85, source_name="UX Strategy",
                tags=("ux", "navigation", "flow", "structure"),
            ),
        ]
        for page in bundle.pages:
            cta = page.get("primary_cta") or ""
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.UX_STRATEGY, external_ref=f"{ref}:page:{page['page']}",
                    claim=f"{page['page']} page: {page.get('objective', '')} (CTA: {cta}).",
                    confidence=0.85, source_name="UX Strategy",
                    tags=(page["page"], "ux", "goal", "cta", "conversion"),
                )
            )
        return signals
