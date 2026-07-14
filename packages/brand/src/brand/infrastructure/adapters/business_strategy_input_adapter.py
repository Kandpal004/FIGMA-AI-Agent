"""BusinessStrategyInputAdapter — feeds Phase-7 Business Strategy into the brand.

Implements :class:`BusinessStrategyInputPort` over the Phase-7 strategy facade: it pulls
a business strategy's neutral design-directive bundle and translates its tier,
positioning, tone, emotions, required trust, and prioritized decisions into
:class:`RawSignal` s (provenance ``BUSINESS_STRATEGY``). The adapter is bound to a
resolved strategy report (the one produced for the project); the brand domain never
imports Phase 7, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from strategy.domain.shared.ids import StrategyReportId
from strategy.interfaces.strategy_facade import StrategyFacade

from brand.application.contracts import RawSignal
from brand.domain.context.context import ProjectContext
from brand.domain.shared.value_objects import ProvenanceKind

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
                provenance=ProvenanceKind.BUSINESS_STRATEGY,
                external_ref=f"{ref}:positioning",
                claim=bundle.positioning_statement,
                confidence=0.9,
                source_name="Business Strategy",
                tags=(bundle.tier, "positioning", "brand"),
            ),
            RawSignal(
                provenance=ProvenanceKind.BUSINESS_STRATEGY,
                external_ref=f"{ref}:message",
                claim=bundle.primary_message,
                confidence=0.85,
                source_name="Business Strategy",
                tags=("message", "value", "voice"),
            ),
            RawSignal(
                provenance=ProvenanceKind.BUSINESS_STRATEGY,
                external_ref=f"{ref}:tone",
                claim=f"The brand tone should be {bundle.tone}.",
                confidence=0.8,
                source_name="Business Strategy",
                tags=(bundle.tone, "tone", "voice"),
            ),
        ]
        for emotion in bundle.emotions:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.BUSINESS_STRATEGY,
                    external_ref=f"{ref}:emotion:{emotion}",
                    claim=f"The experience should evoke {emotion}.",
                    confidence=0.8,
                    source_name="Business Strategy",
                    tags=(emotion, "emotion", "feel"),
                )
            )
        for trust in bundle.required_trust:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.BUSINESS_STRATEGY,
                    external_ref=f"{ref}:trust:{trust}",
                    claim=f"The brand must provide {trust} as a trust signal.",
                    confidence=0.85,
                    source_name="Business Strategy",
                    tags=(trust, "trust"),
                )
            )
        for decision in bundle.prioritized_decisions:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.BUSINESS_STRATEGY,
                    external_ref=decision.id,
                    claim=decision.statement,
                    confidence=decision.confidence,
                    statement=decision.rationale,
                    source_name=f"Strategy: {decision.type}",
                    tags=(decision.type, "strategy", "brand"),
                )
            )
        return signals
