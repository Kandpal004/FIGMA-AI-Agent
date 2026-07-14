"""The Fogg Behavior Model — B = Motivation × Ability × Prompt.

A :class:`FoggAnalysis` is the strategic conclusion drawn from the behavior matrix: when
target behaviors are not happening, is the lever to raise *motivation*, increase
*ability* (reduce friction), or fix the *prompt*? Fogg's insight is that increasing
ability is usually cheaper and more reliable than increasing motivation — this analysis
names which lever to pull.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId

__all__ = ["FoggAnalysis", "FoggLever", "InvalidFoggError"]


class InvalidFoggError(DesignDirectorError):
    """Raised when a Fogg analysis is constructed with invalid data."""

    code = "invalid_fogg_analysis"
    http_status = 422


class FoggLever(str, Enum):
    """The lever the Fogg model recommends pulling."""

    INCREASE_ABILITY = "increase_ability"
    INCREASE_MOTIVATION = "increase_motivation"
    FIX_PROMPT = "fix_prompt"


@dataclass(frozen=True, slots=True)
class FoggAnalysis:
    """The cited strategic conclusion of the Fogg model.

    Attributes:
        primary_lever: The lever most worth pulling to drive the target behavior.
        conclusion: The reasoning behind it.
        ability_barriers: The barriers to ability (friction) to remove.
        prompt_strategy: How prompts should be designed.
        evidence_ids: The evidence supporting it.
    """

    primary_lever: FoggLever
    conclusion: str
    ability_barriers: tuple[str, ...] = ()
    prompt_strategy: str = ""
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.conclusion or not self.conclusion.strip():
            raise InvalidFoggError("FoggAnalysis.conclusion must be non-empty.")
        object.__setattr__(self, "ability_barriers", tuple(self.ability_barriers))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
