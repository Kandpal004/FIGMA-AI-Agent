"""Component contract value objects — a component's data contract and definition of done.

These make a component's inputs, outputs, and success/failure conditions explicit: the data it
requires, the artifacts it produces, and the measurable conditions that decide whether it works.
They are abstract — data *kinds* and *names*, never schemas or bindings.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.value_objects import DataKind, IOKind

__all__ = [
    "ExpectedOutput",
    "FailureCriterion",
    "InvalidContractError",
    "RequiredInput",
    "SuccessCriterion",
]


class InvalidContractError(DesignDirectorError):
    """Raised when a contract value object is constructed with invalid data."""

    code = "invalid_component_intelligence_contract"
    http_status = 422


@dataclass(frozen=True, slots=True)
class RequiredInput:
    """A kind of data the component needs supplied.

    Attributes:
        kind: The data kind.
        description: What the data is used for.
        required: Whether the component cannot function without it.
    """

    kind: DataKind
    description: str = ""
    required: bool = True


@dataclass(frozen=True, slots=True)
class ExpectedOutput:
    """An artifact the component produces.

    Attributes:
        kind: The kind of artifact.
        name: Its abstract name (e.g. "add_to_cart", "selected_variant").
    """

    kind: IOKind
    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidContractError("ExpectedOutput.name must be non-empty.")


@dataclass(frozen=True, slots=True)
class SuccessCriterion:
    """A measurable condition under which the component is considered a success."""

    statement: str

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidContractError("SuccessCriterion.statement must be non-empty.")


@dataclass(frozen=True, slots=True)
class FailureCriterion:
    """A condition under which the component is considered a failure."""

    statement: str

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidContractError("FailureCriterion.statement must be non-empty.")
