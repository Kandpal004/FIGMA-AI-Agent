"""Stage — Friction & Drop-off analysis.

Lifts the friction and exit risk carried by the journey stages into explicit
:class:`FrictionAnalysis` and :class:`DropoffAnalysis`. The psychology-derived friction on
each stage becomes a located, remediable friction point; each stage's exit risk becomes a
scored drop-off risk. Every derived item carries the evidence of the stage it came from.
"""

from __future__ import annotations

from ux.domain.analysis.dropoff import DropoffAnalysis, DropoffRisk
from ux.domain.analysis.friction import FrictionAnalysis, FrictionPoint
from ux.domain.journey.journey import JourneyStage
from ux.domain.journey.journeys import JourneyMap
from ux.domain.shared.ids import FrictionPointId
from ux.domain.shared.value_objects import (
    DropoffKind,
    FrictionKind,
    Impact,
    Severity,
)

__all__ = ["AnalysisBuilder"]

_FRICTION_KEYWORDS: tuple[tuple[str, FrictionKind], ...] = (
    ("checkout", FrictionKind.FORM),
    ("form", FrictionKind.FORM),
    ("field", FrictionKind.FORM),
    ("trust", FrictionKind.TRUST),
    ("proof", FrictionKind.TRUST),
    ("navigat", FrictionKind.NAVIGATION),
    ("find", FrictionKind.NAVIGATION),
    ("load", FrictionKind.PERFORMANCE),
    ("slow", FrictionKind.PERFORMANCE),
    ("choose", FrictionKind.DECISION),
    ("compare", FrictionKind.DECISION),
    ("option", FrictionKind.DECISION),
)

_DROPOFF_KEYWORDS: tuple[tuple[str, DropoffKind], ...] = (
    ("trust", DropoffKind.TRUST_GAP),
    ("price", DropoffKind.COST_SHOCK),
    ("cost", DropoffKind.COST_SHOCK),
    ("complex", DropoffKind.COMPLEXITY),
    ("anxiety", DropoffKind.ANXIETY),
    ("doubt", DropoffKind.ANXIETY),
)


class AnalysisBuilder:
    """Builds the friction and drop-off analyses from the journey map."""

    def build(self, journeys: JourneyMap) -> tuple[FrictionAnalysis, DropoffAnalysis]:
        stages: list[JourneyStage] = []
        for journey in (journeys.conversion, journeys.user, journeys.trust):
            stages.extend(journey)

        friction_points: list[FrictionPoint] = []
        dropoff_risks: list[DropoffRisk] = []
        for stage in stages:
            for friction in stage.friction:
                friction_points.append(
                    FrictionPoint(
                        id=FrictionPointId.new(),
                        location=friction,
                        kind=self._friction_kind(friction),
                        severity=Severity(int(stage.exit_risk)),
                        phase=stage.phase,
                        remedy="Reduce this friction at the point it occurs.",
                        evidence_ids=stage.evidence_ids,
                    )
                )
            if int(stage.exit_risk) >= 2:
                dropoff_risks.append(
                    DropoffRisk(
                        stage=stage.phase,
                        kind=self._dropoff_kind(stage),
                        likelihood=Severity(int(stage.exit_risk)),
                        impact=Impact(min(5, int(stage.exit_risk) + 1)),
                        mitigation="Protect this step with reassurance and reduced effort.",
                        evidence_ids=stage.evidence_ids,
                    )
                )
        return FrictionAnalysis.of(friction_points), DropoffAnalysis.of(dropoff_risks)

    @staticmethod
    def _friction_kind(text: str) -> FrictionKind:
        low = text.lower()
        for key, kind in _FRICTION_KEYWORDS:
            if key in low:
                return kind
        return FrictionKind.COGNITIVE

    @staticmethod
    def _dropoff_kind(stage: JourneyStage) -> DropoffKind:
        haystack = f"{stage.emotion} {' '.join(stage.friction)} {stage.user_goal}".lower()
        for key, kind in _DROPOFF_KEYWORDS:
            if key in haystack:
                return kind
        return DropoffKind.DISTRACTION
