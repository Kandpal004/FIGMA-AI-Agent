"""IAInputAdapter — feeds the Phase-11 Information Architecture into the review.

Implements :class:`IAInputPort` over the Phase-11 IA facade: it pulls the IA report's neutral
wireframe brief bundle and translates its pages and section structure into :class:`RawSignal`
s (provenance ``INFORMATION_ARCHITECTURE``) tagged for hierarchy and structure, so the
information-hierarchy review is grounded. The creative-director domain never imports Phase 11,
so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from ia.domain.shared.ids import IAReportId
from ia.interfaces.ia_facade import IAFacade

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext
from creative_director.domain.shared.value_objects import ProvenanceKind

__all__ = ["IAInputAdapter"]


class IAInputAdapter:
    """Implements :class:`IAInputPort` over a Phase-11 IA report."""

    def __init__(self, facade: IAFacade, report_id: IAReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.wireframe_brief_bundle(self._report_id)
        ref = str(self._report_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.INFORMATION_ARCHITECTURE, external_ref=f"{ref}:hierarchy",
                claim="The information architecture defines a clear page and section hierarchy.",
                confidence=0.88, source_name="Information Architecture",
                tags=("hierarchy", "priority", "structure", "section", "order", "navigation"),
            ),
        ]
        for page in bundle.pages:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.INFORMATION_ARCHITECTURE,
                    external_ref=f"{ref}:page:{page['page_type']}",
                    claim=f"{page['page_type']} page structure: {page.get('purpose', '')}.",
                    confidence=0.85, source_name="Information Architecture",
                    tags=(page["page_type"], "hierarchy", "structure", "section", "priority"),
                )
            )
        return signals
