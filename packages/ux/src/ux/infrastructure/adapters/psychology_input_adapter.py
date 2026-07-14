"""PsychologyInputAdapter — feeds Phase-9 Customer Psychology into the UX strategy.

Implements :class:`PsychologyInputPort` over the Phase-9 psychology facade: it pulls a
psychology model's neutral UX directive bundle and translates its awareness, journey
stages (with friction/trust/emotion), objections, decision triggers, and feasible
behaviors into :class:`RawSignal` s (provenance ``PSYCHOLOGY``). The adapter is bound to a
resolved psychology report; the UX domain never imports Phase 9, so this adapter is the
seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from psychology.domain.shared.ids import PsychologyReportId
from psychology.interfaces.psychology_facade import PsychologyFacade

from ux.application.contracts import RawSignal
from ux.domain.context.context import ProjectContext
from ux.domain.shared.value_objects import ProvenanceKind

__all__ = ["PsychologyInputAdapter"]


class PsychologyInputAdapter:
    """Implements :class:`PsychologyInputPort` over a Phase-9 psychology report."""

    def __init__(self, facade: PsychologyFacade, report_id: PsychologyReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.ux_directive_bundle(self._report_id)
        ref = str(self._report_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:awareness",
                claim=f"The customer is {bundle.awareness} and the market is {bundle.sophistication}.",
                confidence=0.9, source_name="Customer Psychology",
                tags=(bundle.awareness, bundle.sophistication, "awareness"),
            ),
            RawSignal(
                provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:target",
                claim=bundle.target_customer, confidence=0.85, source_name="Customer Psychology",
                tags=("customer", "goal", bundle.intent),
            ),
        ]
        for stage in bundle.journey_stages:
            frictions = ", ".join(stage.get("frictions", ())) or "none"
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY,
                    external_ref=f"{ref}:stage:{stage['phase']}",
                    claim=f"At {stage['phase']}: goal '{stage['goal']}', emotion {stage.get('emotion', '')}, friction: {frictions}.",
                    confidence=0.85, source_name="Customer Psychology",
                    tags=(stage["phase"], stage.get("emotion", ""), "journey", "friction", "trust"),
                )
            )
        for obj in bundle.objections:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:objection:{obj['phase']}",
                    claim=f"Objection: {obj['objection']} — resolve by {obj['resolution']}.",
                    confidence=0.8, source_name="Customer Psychology",
                    tags=(obj["phase"], "objection", "trust"),
                )
            )
        for trigger in bundle.decision_triggers:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:trigger:{trigger['phase']}",
                    claim=f"Decision trigger: {trigger['description']} (activates {trigger['activates']}).",
                    confidence=0.8, source_name="Customer Psychology",
                    tags=(trigger["phase"], trigger["activates"], "decision", "cta"),
                )
            )
        for behavior in bundle.feasible_behaviors:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.PSYCHOLOGY, external_ref=f"{ref}:behavior:{behavior['behavior']}",
                    claim=f"Feasible behavior: {behavior['behavior']} (prompt: {behavior['prompt']}).",
                    confidence=0.8, source_name="Customer Psychology",
                    tags=("behavior", "conversion", "cta"),
                )
            )
        return signals
