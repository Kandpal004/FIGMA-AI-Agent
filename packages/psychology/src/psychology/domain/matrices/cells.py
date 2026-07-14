"""Matrix cells — the typed rows of the nine psychology matrices.

Each cell is a small, cited value object: one objection with its resolution, one trust
requirement with the signal that satisfies it, one motivation mapped to a Maslow need,
one target behavior scored by Fogg, and so on. The matrices in
:mod:`psychology.domain.matrices.matrices` are immutable collections of these cells.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import MatrixCellId, PsychologyEvidenceId
from psychology.domain.shared.value_objects import (
    Confidence,
    DriverKind,
    EmotionKind,
    FeasibilityBand,
    Intensity,
    JourneyPhase,
    Likelihood,
    MaslowNeed,
    ObjectionKind,
    RiskKind,
    TrustRequirementKind,
)

__all__ = [
    "BehaviorCell",
    "ConfidenceCell",
    "EmotionCell",
    "InvalidCellError",
    "MotivationCell",
    "ObjectionCell",
    "RetentionCell",
    "RiskCell",
    "TrustCell",
    "ValueCell",
]


class InvalidCellError(DesignDirectorError):
    """Raised when a matrix cell is constructed with invalid data."""

    code = "invalid_matrix_cell"
    http_status = 422


def _require(value: str, field: str) -> None:
    if not value or not value.strip():
        raise InvalidCellError(f"{field} must be non-empty.")


@dataclass(frozen=True, slots=True)
class ObjectionCell:
    """One objection paired with its resolution strategy."""

    id: MatrixCellId
    objection: str
    kind: ObjectionKind
    phase: JourneyPhase
    resolution_strategy: str
    confidence: Confidence = Confidence(0.7)
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.objection, "ObjectionCell.objection")
        _require(self.resolution_strategy, "ObjectionCell.resolution_strategy")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class TrustCell:
    """One trust requirement paired with the signal that satisfies it."""

    id: MatrixCellId
    requirement: str
    kind: TrustRequirementKind
    signal_needed: str
    phase: JourneyPhase
    salience: Intensity = Intensity(3)
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.requirement, "TrustCell.requirement")
        _require(self.signal_needed, "TrustCell.signal_needed")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class MotivationCell:
    """One motivation mapped to its Maslow need and driver kind."""

    id: MatrixCellId
    motivation: str
    maslow_need: MaslowNeed
    driver_kind: DriverKind
    intensity: Intensity = Intensity(3)
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.motivation, "MotivationCell.motivation")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class EmotionCell:
    """One emotion at a phase, with its trigger and the intended shift."""

    id: MatrixCellId
    emotion: EmotionKind
    phase: JourneyPhase
    trigger: str
    intended_shift: EmotionKind
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.trigger, "EmotionCell.trigger")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BehaviorCell:
    """One target behavior scored by the Fogg model (B = M × A × Prompt)."""

    id: MatrixCellId
    target_behavior: str
    motivation: Intensity
    ability: Intensity
    prompt: str
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.target_behavior, "BehaviorCell.target_behavior")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def has_prompt(self) -> bool:
        return bool(self.prompt and self.prompt.strip())

    @property
    def feasibility(self) -> FeasibilityBand:
        """Fogg feasibility: a behavior happens when motivation, ability, and a prompt
        coincide."""
        if not self.has_prompt:
            return FeasibilityBand.UNLIKELY
        if int(self.motivation) >= 3 and int(self.ability) >= 3:
            return FeasibilityBand.LIKELY
        if int(self.motivation) + int(self.ability) >= 5:
            return FeasibilityBand.POSSIBLE
        return FeasibilityBand.UNLIKELY


@dataclass(frozen=True, slots=True)
class RiskCell:
    """One perceived risk with its likelihood, impact, and mitigation."""

    id: MatrixCellId
    risk: str
    kind: RiskKind
    likelihood: Likelihood
    impact: Intensity
    mitigation: str = ""
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.risk, "RiskCell.risk")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def severity(self) -> int:
        return int(self.likelihood) * int(self.impact)


@dataclass(frozen=True, slots=True)
class ValueCell:
    """One value perception and how it should be framed against price."""

    id: MatrixCellId
    value_perception: str
    price_relation: str
    framing: str = ""
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.value_perception, "ValueCell.value_perception")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ConfidenceCell:
    """One confidence factor with its current level and the lever that raises it."""

    id: MatrixCellId
    factor: str
    current_level: Intensity
    lever: str
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.factor, "ConfidenceCell.factor")
        _require(self.lever, "ConfidenceCell.lever")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class RetentionCell:
    """One retention driver at a lifecycle stage with its mechanism."""

    id: MatrixCellId
    driver: str
    lifecycle_stage: str
    mechanism: str
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.driver, "RetentionCell.driver")
        _require(self.mechanism, "RetentionCell.mechanism")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
