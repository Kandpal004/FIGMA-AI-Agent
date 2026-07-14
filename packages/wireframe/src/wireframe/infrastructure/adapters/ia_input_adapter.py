"""IAInputAdapter — feeds the Phase-11 Information Architecture into the wireframe plan.

Implements :class:`IAInputPort` over the Phase-11 IA facade: it pulls an IA report's neutral
wireframe brief bundle and translates its pages, per-page purposes and section structure,
navigation, and relationships into :class:`RawSignal` s (provenance
``INFORMATION_ARCHITECTURE``). This is the plan's principal input — the wireframe executes the
information architecture. The wireframe domain never imports Phase 11, so this adapter is the
seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from ia.domain.shared.ids import IAReportId
from ia.interfaces.ia_facade import IAFacade

from wireframe.application.contracts import RawSignal
from wireframe.domain.context.context import ProjectContext
from wireframe.domain.shared.value_objects import ProvenanceKind

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
                provenance=ProvenanceKind.INFORMATION_ARCHITECTURE, external_ref=f"{ref}:navigation",
                claim="Global navigation and breadcrumbs structure the wayfinding.",
                confidence=0.85, source_name="Information Architecture",
                tags=("navigation", "structure", "nav", "breadcrumb"),
            ),
        ]
        for page in bundle.pages:
            page_type = page["page_type"]
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.INFORMATION_ARCHITECTURE,
                    external_ref=f"{ref}:page:{page_type}",
                    claim=f"{page_type} page: {page.get('purpose', '')}.",
                    confidence=0.9, source_name="Information Architecture",
                    tags=(page_type, "page", "section", "structure", "navigation", "content"),
                )
            )
            for section in page.get("required_sections", ()):
                stype = section.get("type", "")
                signals.append(
                    RawSignal(
                        provenance=ProvenanceKind.INFORMATION_ARCHITECTURE,
                        external_ref=f"{ref}:section:{page_type}:{stype}",
                        claim=f"{stype} section on {page_type}: {section.get('purpose', '')}.",
                        confidence=0.85, source_name="Information Architecture",
                        tags=(stype, "section", "structure", "content", page_type),
                    )
                )
        for rel in bundle.relationships:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.INFORMATION_ARCHITECTURE,
                    external_ref=f"{ref}:rel:{rel['source']}:{rel['target']}:{rel['kind']}",
                    claim=f"{rel['kind']} relationship from {rel['source']} to {rel['target']}.",
                    confidence=0.8, source_name="Information Architecture",
                    tags=(rel["kind"], "relationship", "recommendation", "navigation"),
                )
            )
        return signals
