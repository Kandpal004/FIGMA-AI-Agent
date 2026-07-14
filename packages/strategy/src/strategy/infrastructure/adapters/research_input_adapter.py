"""ResearchInputAdapter — feeds Phase-6 Research evidence into strategy.

Implements :class:`ResearchInputPort` over the Phase-6 research facade: it pulls a
research report's neutral reasoning bundle and translates its evidence into
:class:`RawInsight` s (provenance ``RESEARCH``). The adapter is bound to a resolved
research report (the one produced for the project); the strategy domain never imports
Phase 6, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from research.domain.shared.ids import ResearchReportId
from research.interfaces.research_facade import ResearchFacade

from strategy.application.contracts import RawInsight
from strategy.domain.context.context import ProjectContext
from strategy.domain.shared.value_objects import ProvenanceKind

__all__ = ["ResearchInputAdapter"]


class ResearchInputAdapter:
    """Implements :class:`ResearchInputPort` over a Phase-6 research report."""

    def __init__(self, facade: ResearchFacade, report_id: ResearchReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawInsight]:
        bundle = await self._facade.reasoning_bundle(self._report_id)
        return [
            RawInsight(
                provenance=ProvenanceKind.RESEARCH,
                external_ref=evidence.id,
                claim=evidence.claim,
                confidence=evidence.confidence,
                statement=evidence.snippet,
                source_name=f"Research: {evidence.provider}",
                tags=(evidence.category, *evidence.tags),
            )
            for evidence in bundle.evidence
        ]
