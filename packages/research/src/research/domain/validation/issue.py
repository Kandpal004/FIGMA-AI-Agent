"""Validation issues and outcomes.

The validation stage produces, per artifact, a :class:`ValidationOutcome`: whether
the artifact is valid and the :class:`ValidationIssue` s found. Issues carry a
severity — ``INFO`` / ``WARN`` / ``ERROR``. An ``ERROR`` rejects the artifact; a
``WARN`` keeps it but penalises its quality score. Issues are retained on the
produced result for auditability — nothing is silently dropped.

Pure domain: standard library and the shared-kernel error base only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.errors import DesignDirectorError

__all__ = ["InvalidValidationError", "IssueSeverity", "ValidationIssue", "ValidationOutcome"]


class InvalidValidationError(DesignDirectorError):
    """Raised when a validation issue is constructed with invalid data."""

    code = "invalid_validation"
    http_status = 422


class IssueSeverity(str, Enum):
    """The severity of a validation issue."""

    INFO = "info"
    WARN = "warn"
    ERROR = "error"

    @property
    def rank(self) -> int:
        return {IssueSeverity.INFO: 0, IssueSeverity.WARN: 1, IssueSeverity.ERROR: 2}[self]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One issue found while validating an artifact.

    Attributes:
        severity: How serious the issue is.
        code: A stable, machine-readable code.
        message: A human-readable description.
        field: The field the issue concerns, if any.
    """

    severity: IssueSeverity
    code: str
    message: str
    field: str = ""

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise InvalidValidationError("ValidationIssue.code must be non-empty.")


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    """The result of validating an artifact.

    Attributes:
        issues: The issues found (empty means clean).
    """

    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "issues", tuple(self.issues))

    @property
    def is_valid(self) -> bool:
        """Whether the artifact passes (no ERROR-severity issues)."""
        return not self.has_errors

    @property
    def has_errors(self) -> bool:
        return any(i.severity is IssueSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity is IssueSeverity.WARN for i in self.issues)

    def errors(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity is IssueSeverity.ERROR)

    def warnings(self) -> tuple[ValidationIssue, ...]:
        return tuple(i for i in self.issues if i.severity is IssueSeverity.WARN)
