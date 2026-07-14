"""BusinessStrategyInputAdapter — feeds Phase-7 Business Strategy into the IA.

Implements :class:`BusinessStrategyInputPort` over the Phase-7 strategy facade: it pulls a
strategy's neutral directive bundle and translates its positioning, message, and prioritized
decisions into :class:`RawSignal` s (provenance ``BUSINESS_STRATEGY``). The adapter is bound
to a resolved strategy report; the IA domain never imports Phase 7, so this adapter is the
seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from strategy.domain.shared.ids import StrategyReportId
from strategy.interfaces.strategy_facade import StrategyFacade

from ia.application.contracts import RawSignal
from ia.domain.context.context import ProjectContext
from ia.domain.shared.value_objects import ProvenanceKind

__all__ = ["BusinessStrategyInputAdapter"]


class BusinessStrategyInputAdapter:
    """Implements :class:`BusinessStrategyInputPort` over a Phase-7 strategy report."""

    def __init__(self, facade: StrategyFacade, report_id: StrategyReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.directive_bundle(self._report_id)
        ref = str(self._report_id)
        return [
            RawSignal(
                provenance=ProvenanceKind.BUSINESS_STRATEGY, external_ref=f"{ref}:positioning",
                claim=bundle.positioning_statement, confidence=0.85, source_name="Business Strategy",
                tags=(bundle.tier, "positioning", "business", "conversion"),
            ),
            RawSignal(
                provenance=ProvenanceKind.BUSINESS_STRATEGY, external_ref=f"{ref}:goal",
                claim="Increase conversion and average order value.", confidence=0.85,
                source_name="Business Strategy", tags=("conversion", "aov", "business", "revenue"),
            ),
        ]
