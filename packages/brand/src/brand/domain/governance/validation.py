"""Brand validation rules — the machine-checkable brand contract.

A :class:`BrandValidationRule` is a structured, checkable assertion about a subject
("every primary CTA MUST express the component personality", "no forbidden word appears
in copy", "contrast MUST satisfy the colour philosophy"). It is a *spec*, not executable
code — the stable contract a downstream Design-System / UI / QA phase enforces
automatically. The :class:`ValidationRuleSet` is the immutable collection.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId, ValidationRuleId
from brand.domain.shared.value_objects import RuleEnforcement, ValidationSeverity

__all__ = [
    "BrandValidationRule",
    "InvalidValidationError",
    "ValidationRuleSet",
]


class InvalidValidationError(DesignDirectorError):
    """Raised when a validation rule is constructed with invalid data."""

    code = "invalid_validation_rule"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandValidationRule:
    """One cited, machine-checkable validation rule (a spec, not executable code).

    Attributes:
        id: Rule identity.
        subject: What the rule is about (e.g. "primary_cta", "copy", "contrast").
        assertion: The assertion that must hold.
        enforcement: RFC-2119 strength of the assertion.
        severity: The severity of a breach.
        checkable_hint: A hint for how a downstream engine can check it.
        evidence_ids: The evidence supporting it.
    """

    id: ValidationRuleId
    subject: str
    assertion: str
    enforcement: RuleEnforcement = RuleEnforcement.MUST
    severity: ValidationSeverity = ValidationSeverity.ERROR
    checkable_hint: str = ""
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.subject or not self.subject.strip():
            raise InvalidValidationError("BrandValidationRule.subject must be non-empty.")
        if not self.assertion or not self.assertion.strip():
            raise InvalidValidationError("BrandValidationRule.assertion must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ValidationRuleSet:
    """An immutable set of validation rules."""

    rules: tuple[BrandValidationRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))

    @classmethod
    def of(cls, rules: Iterable[BrandValidationRule]) -> ValidationRuleSet:
        return cls(rules=tuple(rules))

    def __len__(self) -> int:
        return len(self.rules)

    def __iter__(self):
        return iter(self.rules)

    def blocking(self) -> tuple[BrandValidationRule, ...]:
        """Rules whose breach is an error (must block downstream sign-off)."""
        return tuple(r for r in self.rules if r.severity is ValidationSeverity.ERROR)

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return tuple(eid for r in self.rules for eid in r.evidence_ids)
