"""UXInputAdapter — feeds the Phase-10 UX Strategy into the engine.

Implements :class:`UXInputPort` over the Phase-10 UX facade, translating the design brief into
:class:`RawSignal` s (provenance ``UX_STRATEGY``). The component-intelligence domain never
imports Phase 10, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from ux.domain.shared.ids import UXReportId
from ux.interfaces.ux_facade import UXFacade

from component_intelligence.application.contracts import RawSignal
from component_intelligence.domain.context.context import ProjectContext
from component_intelligence.domain.shared.value_objects import ProvenanceKind

__all__ = ["UXInputAdapter"]


class UXInputAdapter:
    """Implements :class:`UXInputPort` over a Phase-10 UX report."""

    def __init__(self, facade: UXFacade, report_id: UXReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.design_brief_bundle(self._report_id)
        ref = str(self._report_id)
        signals: list[RawSignal] = [RawSignal(
            provenance=ProvenanceKind.UX_STRATEGY, external_ref=f"{ref}:goal",
            claim=bundle.primary_user_goal, confidence=0.85, source_name="UX Strategy",
            tags=("ux", "goal", "flow", "interaction"))]
        for page in bundle.pages:
            signals.append(RawSignal(
                provenance=ProvenanceKind.UX_STRATEGY, external_ref=f"{ref}:page:{page['page']}",
                claim=f"{page['page']}: {page.get('objective', '')}.", confidence=0.8,
                source_name="UX Strategy", tags=(page["page"], "ux", "interaction", "flow")))
        return signals
