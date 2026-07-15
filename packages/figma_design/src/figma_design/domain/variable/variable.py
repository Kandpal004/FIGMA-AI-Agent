"""The Variable model — a Figma variable and its per-mode values.

A :class:`Variable` is the Figma expression of a Design-System token: a typed, scoped name whose
value can differ *per mode* (light vs dark, desktop vs mobile). A :class:`VariableValue` is either
a literal *or* an alias to another variable by key — so a semantic variable
(``color.text.default``) aliases a primitive (``gray.900``) exactly as tokens do, and the alias
can differ by mode. This is how a senior designer builds a variable-driven file.

Pure domain: standard library, the shared-kernel error base, FD ids, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.shared.ids import VariableId
from figma_design.domain.shared.value_objects import VariableScope, VariableType

__all__ = ["InvalidVariableError", "Variable", "VariableValue"]

_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidVariableError(DesignDirectorError):
    """Raised when a variable or variable value is constructed with invalid data."""

    code = "invalid_figma_design_variable"
    http_status = 422


def _key(value: str, what: str) -> str:
    normalized = value.strip().lower()
    if not _KEY.match(normalized):
        raise InvalidVariableError(
            f"{what} must be a dotted lower-case key (e.g. 'color.text.default').",
            details={"value": value},
        )
    return normalized


@dataclass(frozen=True, slots=True)
class VariableValue:
    """A variable's value for one mode: either a literal *or* an alias — never both.

    Attributes:
        literal: The concrete value (a colour hex, a number as string, a string, "true"/"false").
            Mutually exclusive with ``ref``.
        ref: The key of the variable this value aliases. Mutually exclusive with ``literal``.
    """

    literal: str | None = None
    ref: str | None = None

    def __post_init__(self) -> None:
        has_literal = self.literal is not None
        has_ref = self.ref is not None
        if has_literal == has_ref:
            raise InvalidVariableError(
                "VariableValue must be exactly one of literal or ref.",
                details={"literal": self.literal, "ref": self.ref},
            )
        if has_literal:
            if not self.literal.strip():
                raise InvalidVariableError("VariableValue.literal must be non-empty.")
        else:
            object.__setattr__(self, "ref", _key(self.ref, "VariableValue.ref"))

    @property
    def is_alias(self) -> bool:
        return self.ref is not None

    @classmethod
    def of(cls, literal: str) -> VariableValue:
        return cls(literal=literal)

    @classmethod
    def alias(cls, ref: str) -> VariableValue:
        return cls(ref=ref)


@dataclass(frozen=True, slots=True)
class Variable:
    """A Figma variable with a value per mode.

    Attributes:
        id: Variable identity within this model.
        key: The dotted, lower-case variable key (unique within its collection).
        type: The resolved variable type (colour / float / string / boolean).
        scopes: Where the variable may be bound (empty means ALL).
        values: The value per mode name (must cover exactly the collection's modes).
        description: Human-readable intent.
    """

    id: VariableId
    key: str
    type: VariableType
    values: Mapping[str, VariableValue]
    scopes: frozenset[VariableScope] = field(default_factory=frozenset)
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _key(self.key, "Variable.key"))
        values = {
            mode.strip(): value
            for mode, value in self.values.items()
            if mode and mode.strip()
        }
        if not values:
            raise InvalidVariableError(
                "A Variable must define a value for at least one mode.",
                details={"key": self.key},
            )
        for mode, value in values.items():
            if value.is_alias and value.ref == self.key:
                raise InvalidVariableError(
                    "A variable cannot alias itself.",
                    details={"key": self.key, "mode": mode},
                )
        object.__setattr__(self, "values", MappingProxyType(values))
        object.__setattr__(self, "scopes", frozenset(self.scopes))

    @property
    def modes(self) -> frozenset[str]:
        return frozenset(self.values.keys())

    @property
    def alias_refs(self) -> tuple[str, ...]:
        """Every variable key this variable aliases across its modes."""
        return tuple(
            dict.fromkeys(v.ref for v in self.values.values() if v.is_alias)
        )

    def permits(self, scope: VariableScope) -> bool:
        return not self.scopes or VariableScope.ALL in self.scopes or scope in self.scopes
