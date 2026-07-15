"""IAInputAdapter — feeds the Phase-11 Information Architecture into the engine.

Implements :class:`IAInputPort` over the Phase-11 IA facade, translating page structure into
:class:`RawSignal` s (provenance ``INFORMATION_ARCHITECTURE``), so page coverage is grounded. The
orchestrator domain never imports Phase 11, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from ia.domain.shared.ids import IAReportId
from ia.interfaces.ia_facade import IAFacade

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext
from design_orchestrator.domain.shared.value_objects import ProvenanceKind

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
                provenance=ProvenanceKind.INFORMATION_ARCHITECTURE,
                external_ref=f"{ref}:hierarchy",
                claim="The information architecture defines the pages the plan must cover.",
                confidence=0.85,
                source_name="Information Architecture",
                tags=("page", "coverage", "hierarchy", "structure"),
            )
        ]
        for page in bundle.pages:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.INFORMATION_ARCHITECTURE,
                    external_ref=f"{ref}:page:{page['page_type']}",
                    claim=f"{page['page_type']} page must be planned.",
                    confidence=0.8,
                    source_name="Information Architecture",
                    tags=(page["page_type"], "page", "coverage"),
                )
            )
        return signals
