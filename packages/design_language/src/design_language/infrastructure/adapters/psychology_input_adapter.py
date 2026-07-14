"""PsychologyInputAdapter — feeds the Phase-9 Customer Psychology into the language.

Implements :class:`PsychologyInputPort` over the Phase-9 psychology facade: it pulls the
psychology model's neutral UX directive bundle and translates its journey stages and objections
into :class:`RawSignal` s (provenance ``PSYCHOLOGY``), so the DNA's emotional and trust posture
is grounded in how the customer feels. The design-language domain never imports Phase 9, so this
adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from psychology.domain.shared.ids import PsychologyReportId
from psychology.interfaces.psychology_facade import PsychologyFacade

from design_language.application.contracts import RawSignal
from design_language.domain.context.context import ProjectContext
from design_language.domain.shared.value_objects import ProvenanceKind

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
        for stage in bundle.journey_stages:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:stage:{stage['phase']}",
                    claim=f"At {stage['phase']}: emotion {stage.get('emotion', '')} — the visual "
                          "language must support this emotional posture.",
                    confidence=0.85, source_name="Customer Psychology",
                    tags=(stage["phase"], "emotion", "trust", "confidence", "calm"),
                )
            )
        for obj in bundle.objections:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:objection:{obj['phase']}",
                    claim=f"Objection at {obj['phase']}: {obj['objection']} — reduce anxiety through "
                          "visual restraint and clarity.",
                    confidence=0.8, source_name="Customer Psychology",
                    tags=(obj["phase"], "anxiety", "trust", "emotion"),
                )
            )
        return signals
