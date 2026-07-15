"""PsychologyInputAdapter — feeds the Phase-9 Customer Psychology into the engine.

Implements :class:`PsychologyInputPort` over the Phase-9 psychology facade, translating
objections into :class:`RawSignal` s (provenance ``PSYCHOLOGY``), so the state, motion, and
interaction tokens are grounded in how the customer feels. The design-system domain never
imports Phase 9, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from psychology.domain.shared.ids import PsychologyReportId
from psychology.interfaces.psychology_facade import PsychologyFacade

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext
from design_system.domain.shared.value_objects import ProvenanceKind

__all__ = ["PsychologyInputAdapter"]


class PsychologyInputAdapter:
    """Implements :class:`PsychologyInputPort` over a Phase-9 psychology report."""

    def __init__(self, facade: PsychologyFacade, report_id: PsychologyReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.ux_directive_bundle(self._report_id)
        ref = str(self._report_id)
        signals: list[RawSignal] = []
        for obj in bundle.objections:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY,
                    external_ref=f"{ref}:objection:{obj['phase']}",
                    claim=f"Objection at {obj['phase']}: {obj['objection']} — feedback and "
                    "motion tokens must reduce this anxiety.",
                    confidence=0.8,
                    source_name="Customer Psychology",
                    tags=(obj["phase"], "state", "motion", "feedback", "trust"),
                )
            )
        if not signals:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY,
                    external_ref=f"{ref}:trust",
                    claim="Clear feedback states and calm motion build trust and reduce friction.",
                    confidence=0.8,
                    source_name="Customer Psychology",
                    tags=("state", "motion", "feedback", "trust"),
                )
            )
        return signals
