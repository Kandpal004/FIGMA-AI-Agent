"""Constraints — the rules every future UI must obey.

The design system does not only describe *what* exists (tokens, components, themes); it also
codifies the *rules* that make it a system rather than a pile of assets. A :class:`Constraint`
is one enforceable rule of a given :class:`ConstraintKind` — use only tokens, never hard-code
values, keep to the spacing grid and the type scale, meet a minimum contrast, mirror under RTL,
satisfy accessibility and performance budgets, keep light/dark at parity — carried at a
:class:`EnforcementLevel` (blocking or recommended) and grounded in cited evidence.

A :class:`ConstraintSet` is the immutable, unique-by-kind registry. It guarantees the
non-negotiable floor is present: ``TOKEN_ONLY`` and ``NO_HARDCODED`` must always be blocking —
a design system that permits hard-coded values is not a design system.

Pure domain: standard library, the shared-kernel error base, DS ids, evidence, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_system.domain.evidence.evidence import Citation
from design_system.domain.shared.ids import ConstraintId
from design_system.domain.shared.value_objects import ConstraintKind, EnforcementLevel

__all__ = ["Constraint", "ConstraintSet", "InvalidConstraintError"]

# The rules that must always be present and blocking.
_MANDATORY_BLOCKING = (ConstraintKind.TOKEN_ONLY, ConstraintKind.NO_HARDCODED)


class InvalidConstraintError(DesignDirectorError):
    """Raised when a constraint or constraint set violates a structural invariant."""

    code = "invalid_design_system_constraint"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Constraint:
    """One enforceable rule of the design system.

    Attributes:
        id: Constraint identity within this specification.
        kind: Which rule this is.
        enforcement: How strictly it is enforced (blocking or recommended).
        statement: The human-readable rule.
        rationale: Why the rule exists.
        parameters: Any rule parameters (e.g. ``{"min_contrast": "4.5"}``,
            ``{"grid": "4px"}``).
        citations: The evidence supporting this rule (must resolve in the evidence graph).
    """

    id: ConstraintId
    kind: ConstraintKind
    enforcement: EnforcementLevel
    statement: str
    rationale: str = ""
    parameters: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    citations: tuple[Citation, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidConstraintError(
                "Constraint.statement must be non-empty.", details={"kind": self.kind.value}
            )
        params = {
            k.strip(): str(v).strip()
            for k, v in self.parameters.items()
            if k and k.strip()
        }
        object.__setattr__(self, "statement", self.statement.strip())
        object.__setattr__(self, "parameters", MappingProxyType(params))
        object.__setattr__(self, "citations", tuple(self.citations))

    @property
    def is_blocking(self) -> bool:
        return self.enforcement is EnforcementLevel.BLOCKING

    @property
    def evidence_ids(self) -> tuple:
        return tuple(c.evidence_id for c in self.citations)


@dataclass(frozen=True, slots=True)
class ConstraintSet:
    """The immutable, unique-by-kind registry of the design system's rules."""

    items: Mapping[ConstraintKind, Constraint] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        data = dict(self.items)
        for kind, constraint in data.items():
            if constraint.kind is not kind:
                raise InvalidConstraintError(
                    "Constraint key must match its kind.",
                    details={"key": kind.value, "constraint": constraint.kind.value},
                )
        for mandatory in _MANDATORY_BLOCKING:
            constraint = data.get(mandatory)
            if constraint is None:
                raise InvalidConstraintError(
                    f"The {mandatory.value} constraint is mandatory.",
                    details={"missing": mandatory.value},
                )
            if not constraint.is_blocking:
                raise InvalidConstraintError(
                    f"The {mandatory.value} constraint must be blocking.",
                    details={"kind": mandatory.value},
                )
        object.__setattr__(self, "items", MappingProxyType(data))

    @classmethod
    def of(cls, constraints: Iterable[Constraint]) -> ConstraintSet:
        mapping: dict[ConstraintKind, Constraint] = {}
        for constraint in constraints:
            if constraint.kind in mapping:
                raise InvalidConstraintError(
                    "Duplicate constraint kind.", details={"kind": constraint.kind.value}
                )
            mapping[constraint.kind] = constraint
        return cls(items=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def __contains__(self, kind: ConstraintKind) -> bool:
        return kind in self.items

    def get(self, kind: ConstraintKind) -> Constraint:
        constraint = self.items.get(kind)
        if constraint is None:
            raise InvalidConstraintError(
                f"No constraint of kind {kind.value}.", details={"kind": kind.value}
            )
        return constraint

    @property
    def kinds(self) -> tuple[ConstraintKind, ...]:
        return tuple(self.items.keys())

    def blocking(self) -> tuple[Constraint, ...]:
        return tuple(c for c in self.items.values() if c.is_blocking)
