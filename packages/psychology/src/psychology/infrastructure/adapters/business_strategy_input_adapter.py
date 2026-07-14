"""BusinessStrategyInputAdapter — feeds Phase-7 Business Strategy into the psychology.

Implements :class:`BusinessStrategyInputPort` over the Phase-7 strategy facade: it pulls a
strategy's neutral directive bundle and translates its positioning, tone, emotions,
required trust, and prioritized decisions into :class:`RawSignal` s (provenance
``BUSINESS_STRATEGY``). The adapter is bound to a resolved strategy report; the psychology
domain never imports Phase 7, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from strategy.domain.shared.ids import StrategyReportId
from strategy.interfaces.strategy_facade import StrategyFacade

from psychology.application.contracts import RawSignal
from psychology.domain.context.context import ProjectContext
from psychology.domain.shared.value_objects import ProvenanceKind

__all__ = ["BusinessStrategyInputAdapter"]


class BusinessStrategyInputAdapter:
    """Implements :class:`BusinessStrategyInputPort` over a Phase-7 strategy report."""

    def __init__(self, facade: StrategyFacade, report_id: StrategyReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.directive_bundle(self._report_id)
        ref = str(self._report_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.BUSINESS_STRATEGY, external_ref=f"{ref}:positioning",
                claim=bundle.positioning_statement, confidence=0.9, source_name="Business Strategy",
                tags=(bundle.tier, "positioning", "value"),
            ),
            RawSignal(
                provenance=ProvenanceKind.BUSINESS_STRATEGY, external_ref=f"{ref}:message",
                claim=bundle.primary_message, confidence=0.85, source_name="Business Strategy",
                tags=("message", "value"),
            ),
        ]
        for emotion in bundle.emotions:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.BUSINESS_STRATEGY, external_ref=f"{ref}:emotion:{emotion}",
                    claim=f"The experience should evoke {emotion}.", confidence=0.8,
                    source_name="Business Strategy", tags=(emotion, "emotion", "feel"),
                )
            )
        for trust in bundle.required_trust:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.BUSINESS_STRATEGY, external_ref=f"{ref}:trust:{trust}",
                    claim=f"The offer must provide {trust} as a trust signal.", confidence=0.85,
                    source_name="Business Strategy", tags=(trust, "trust", "review", "guarantee"),
                )
            )
        for decision in bundle.prioritized_decisions:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.BUSINESS_STRATEGY, external_ref=decision.id,
                    claim=decision.statement, confidence=decision.confidence, statement=decision.rationale,
                    source_name=f"Strategy: {decision.type}", tags=(decision.type, "strategy"),
                )
            )
        return signals
