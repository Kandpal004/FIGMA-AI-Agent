"""PsychologyInputAdapter — feeds the Phase-9 Customer Psychology into the engine.

Implements :class:`PsychologyInputPort` over the Phase-9 facade, translating objections into
:class:`RawSignal` s (provenance ``PSYCHOLOGY``), so trust and conversion sequencing is grounded
in how the customer feels. The orchestrator domain never imports Phase 9, so this adapter is the
seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from psychology.domain.shared.ids import PsychologyReportId
from psychology.interfaces.psychology_facade import PsychologyFacade

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext
from design_orchestrator.domain.shared.value_objects import ProvenanceKind

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
                    claim=f"Objection at {obj['phase']}: {obj['objection']} — trust sections must "
                    "precede the conversion ask.",
                    confidence=0.8,
                    source_name="Customer Psychology",
                    tags=(obj["phase"], "trust", "conversion", "sequence"),
                )
            )
        if not signals:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY,
                    external_ref=f"{ref}:trust",
                    claim="Trust sections must precede the conversion ask.",
                    confidence=0.8,
                    source_name="Customer Psychology",
                    tags=("trust", "conversion", "sequence"),
                )
            )
        return signals
