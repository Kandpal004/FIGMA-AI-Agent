"""Section execution contracts — success/failure criteria, review checklist, and I/O.

These value objects make a section's *definition of done* explicit and auditable, and wire
the section into the execution flow. A section without success criteria and a review
checklist is not a plan — it is a hope; the aggregate refuses to call such a plan usable.

* :class:`SectionIO` — a data/asset/artifact a section consumes or produces (Execution Graph
  wiring).
* :class:`SuccessCriterion` / :class:`FailureCriterion` — the measurable conditions that
  decide whether the built section passed or failed.
* :class:`ChecklistItem` — one item on the section's review checklist.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.shared.value_objects import IOKind

__all__ = [
    "ChecklistItem",
    "FailureCriterion",
    "InvalidCriterionError",
    "SectionIO",
    "SuccessCriterion",
]


class InvalidCriterionError(DesignDirectorError):
    """Raised when a criterion, checklist item, or I/O is constructed with invalid data."""

    code = "invalid_wireframe_criterion"
    http_status = 422


@dataclass(frozen=True, slots=True)
class SectionIO:
    """A data/asset/artifact a section consumes (input) or produces (output).

    Attributes:
        kind: The kind of thing flowing.
        name: Its abstract name (e.g. "selected_variant", "cart_state").
    """

    kind: IOKind
    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidCriterionError("SectionIO.name must be non-empty.")


@dataclass(frozen=True, slots=True)
class SuccessCriterion:
    """A measurable condition under which the built section is considered a success.

    Attributes:
        statement: The condition, phrased so it can be checked.
    """

    statement: str

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidCriterionError("SuccessCriterion.statement must be non-empty.")


@dataclass(frozen=True, slots=True)
class FailureCriterion:
    """A condition under which the built section is considered a failure.

    Attributes:
        statement: The failure condition, phrased so it can be checked.
    """

    statement: str

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidCriterionError("FailureCriterion.statement must be non-empty.")


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    """One item on a section's review checklist.

    Attributes:
        statement: What the reviewer must verify.
        blocking: Whether an unchecked item blocks approval.
    """

    statement: str
    blocking: bool = True

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidCriterionError("ChecklistItem.statement must be non-empty.")
