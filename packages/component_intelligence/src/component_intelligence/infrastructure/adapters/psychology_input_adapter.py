"""PsychologyInputAdapter — feeds the Phase-9 Customer Psychology into the engine.

Implements :class:`PsychologyInputPort` over the Phase-9 psychology facade, translating
objections into :class:`RawSignal` s (provenance ``PSYCHOLOGY``), so trust and friction effects
are grounded in how the customer feels. The component-intelligence domain never imports Phase 9,
so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from psychology.domain.shared.ids import PsychologyReportId
from psychology.interfaces.psychology_facade import PsychologyFacade

from component_intelligence.application.contracts import RawSignal
from component_intelligence.domain.context.context import ProjectContext
from component_intelligence.domain.shared.value_objects import ProvenanceKind

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
            signals.append(RawSignal(
                provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:objection:{obj['phase']}",
                claim=f"Objection at {obj['phase']}: {obj['objection']} — components must reduce this anxiety.",
                confidence=0.8, source_name="Customer Psychology",
                tags=(obj["phase"], "trust", "conversion", "friction", "emotion")))
        if not signals:
            signals.append(RawSignal(
                provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:trust",
                claim="Trust and low friction drive conversion.", confidence=0.8,
                source_name="Customer Psychology", tags=("trust", "conversion", "friction", "emotion")))
        return signals
