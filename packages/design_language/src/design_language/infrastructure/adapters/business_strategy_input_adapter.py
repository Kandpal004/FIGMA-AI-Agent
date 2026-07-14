"""BusinessStrategyInputAdapter — feeds the Phase-7 Business Strategy into the language.

Implements :class:`BusinessStrategyInputPort` over the Phase-7 strategy facade: it pulls a
strategy's neutral directive bundle and translates its positioning and commercial goals into
:class:`RawSignal` s (provenance ``BUSINESS_STRATEGY``), so the language selection is grounded
in how the visual language maximises the business goals. The design-language domain never
imports Phase 7, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from strategy.domain.shared.ids import StrategyReportId
from strategy.interfaces.strategy_facade import StrategyFacade

from design_language.application.contracts import RawSignal
from design_language.domain.context.context import ProjectContext
from design_language.domain.shared.value_objects import ProvenanceKind

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
                tags=(bundle.tier, "business", "positioning", "conversion"),
            ),
            RawSignal(
                provenance=ProvenanceKind.BUSINESS_STRATEGY, external_ref=f"{ref}:goal",
                claim="The visual language must advance conversion and premium positioning.",
                confidence=0.85, source_name="Business Strategy",
                tags=("business", "conversion", "revenue", "positioning"),
            ),
        ]
