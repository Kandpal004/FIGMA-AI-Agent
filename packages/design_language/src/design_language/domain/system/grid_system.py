"""The Grid System — the structural grid the language composes on.

A :class:`GridSystem` fixes the column count, the alignment posture, and the gutter/margin/
container rhythm — all in modular steps, no pixels. It is the skeleton every future layout
snaps to.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId
from design_language.domain.shared.value_objects import AlignmentApproach

__all__ = ["GridSystem", "InvalidGridError"]


class InvalidGridError(DesignDirectorError):
    """Raised when a grid system is constructed with invalid data."""

    code = "invalid_design_language_grid"
    http_status = 422


@dataclass(frozen=True, slots=True)
class GridSystem:
    """The structural grid of the design language.

    Attributes:
        columns: The base column count (e.g. 12).
        alignment: The alignment posture the grid enforces.
        gutter_steps: The gutter width in spacing steps.
        margin_steps: The outer margin in spacing steps.
        max_container_steps: The maximum container width in spacing steps.
        evidence_ids: The evidence grounding the grid.
    """

    columns: int = 12
    alignment: AlignmentApproach = AlignmentApproach.BASELINE
    gutter_steps: int = 3
    margin_steps: int = 4
    max_container_steps: int = 160
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        for name in ("columns", "gutter_steps", "margin_steps", "max_container_steps"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise InvalidGridError(
                    f"GridSystem.{name} must be a positive int.", details={"value": value}
                )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids
