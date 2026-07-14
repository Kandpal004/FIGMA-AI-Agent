"""The Framework Lens — the consolidated behavioral-science analysis.

:class:`FrameworkLens` groups the applied frameworks — the Maslow mapping, the Fogg
analysis, the Hook loop, and the behavioral-economics principles — into one cohesive,
cited value object the report composes. (The JTBD framework is applied through the
:mod:`psychology.domain.persona.jtbd` models, which the report carries directly.)

Pure domain: standard library and the framework sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from psychology.domain.frameworks.behavioral_economics import BehavioralPrincipleSet
from psychology.domain.frameworks.fogg import FoggAnalysis, FoggLever
from psychology.domain.frameworks.hook import HookLoop
from psychology.domain.frameworks.maslow import MaslowMapping
from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import (
    MaslowNeed,
    PsychFramework,
)

__all__ = ["FrameworkLens"]


def _default_fogg() -> FoggAnalysis:
    return FoggAnalysis(
        primary_lever=FoggLever.INCREASE_ABILITY,
        conclusion="Reduce friction to make the target behavior easier.",
    )


def _default_hook() -> HookLoop:
    return HookLoop(
        trigger="a reminder to return",
        action="revisit the offer",
        variable_reward="discover something new or relevant",
        investment="save preferences or items",
    )


@dataclass(frozen=True, slots=True)
class FrameworkLens:
    """The consolidated, cited behavioral-science analysis.

    Attributes:
        maslow: The Maslow-need mapping.
        fogg: The Fogg behavior analysis.
        hook: The habit-forming loop.
        principles: The applied behavioral-economics principles.
    """

    maslow: MaslowMapping = field(default_factory=lambda: MaslowMapping(MaslowNeed.SAFETY))
    fogg: FoggAnalysis = field(default_factory=_default_fogg)
    hook: HookLoop = field(default_factory=_default_hook)
    principles: BehavioralPrincipleSet = field(default_factory=BehavioralPrincipleSet)

    def applied_frameworks(self) -> frozenset[PsychFramework]:
        """The frameworks this lens has actually applied."""
        applied = {PsychFramework.MASLOW, PsychFramework.FOGG, PsychFramework.HOOK}
        if len(self.principles):
            applied.add(PsychFramework.BEHAVIORAL_ECONOMICS)
        return frozenset(applied)

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return (
            *self.maslow.evidence_ids,
            *self.fogg.evidence_ids,
            *self.hook.evidence_ids,
            *self.principles.evidence_ids(),
        )
