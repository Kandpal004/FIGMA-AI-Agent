"""The UX Directive Bundle — the neutral brief downstream UX/CRO phases consume.

The Customer Psychology Engine is the foundation every UX and CRO decision must derive
from — but it must not depend on those phases. So it emits a :class:`UXDirectiveBundle`:
a flat, self-contained projection of the psychology that matters to UX/CRO — the
awareness and sophistication (message match), the phased journey with per-stage anxiety /
friction / trust / emotion, the objection→resolution map, the prioritised decision
triggers, and the Fogg-feasible target behaviors with their ethical levers — which
downstream engines *pull* and adapt through ports they own. This keeps the dependency
arrows pointing only into psychology.

Pure domain: standard library and the report/section models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from psychology.domain.journey.buying_journey import BuyingStage
from psychology.domain.matrices.cells import BehaviorCell, ObjectionCell
from psychology.domain.report.report import CustomerPsychologyReport
from psychology.domain.shared.ids import PsychologyReportId
from psychology.domain.shared.value_objects import (
    AwarenessLevel,
    CustomerIntent,
    SophisticationLevel,
)
from psychology.domain.state.confidence import DecisionTrigger

__all__ = ["UXDirectiveBundle"]


@dataclass(frozen=True, slots=True)
class UXDirectiveBundle:
    """A flat, neutral projection of a psychology report for downstream UX/CRO.

    Attributes:
        report_id: The report this bundle projects.
        project_id: The project the psychology served.
        target_customer: Who is deciding.
        awareness: The awareness level (message match).
        sophistication: The market sophistication.
        intent: The customer's purchase intent.
        journey_stages: The buying journey stages with their friction/trust/emotion.
        objections: The objection→resolution map.
        decision_triggers: The prioritised triggers that move the customer forward.
        feasible_behaviors: The Fogg-feasible target behaviors CRO can rely on.
        is_usable: Whether the model is cleared to drive UX/CRO.
        created_at: When the model was produced.
    """

    report_id: PsychologyReportId
    project_id: str
    target_customer: str
    awareness: AwarenessLevel
    sophistication: SophisticationLevel
    intent: CustomerIntent
    journey_stages: tuple[BuyingStage, ...]
    objections: tuple[ObjectionCell, ...]
    decision_triggers: tuple[DecisionTrigger, ...]
    feasible_behaviors: tuple[BehaviorCell, ...]
    is_usable: bool
    created_at: datetime

    @classmethod
    def from_report(cls, report: CustomerPsychologyReport) -> UXDirectiveBundle:
        """Project a :class:`CustomerPsychologyReport` into a UX directive bundle."""
        return cls(
            report_id=report.id,
            project_id=report.project_id,
            target_customer=report.profile.target_customer,
            awareness=report.profile.awareness,
            sophistication=report.profile.sophistication,
            intent=report.profile.intent,
            journey_stages=tuple(report.buying_journey),
            objections=tuple(report.matrices.objection),
            decision_triggers=report.profile.decision_triggers,
            feasible_behaviors=report.matrices.behavior.feasible(),
            is_usable=report.is_usable,
            created_at=report.created_at,
        )

    @property
    def is_empty(self) -> bool:
        return not self.journey_stages
