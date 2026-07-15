"""The Variable Collection model — a named set of variables and their modes.

A :class:`VariableCollection` groups variables under a shared set of *modes* — the Figma way of
expressing "the same variable, different value in light vs dark, or desktop vs mobile". The engine
builds a handful of collections a senior designer would: a Primitive collection, a Semantic
collection, a Theme collection with Light/Dark modes, and a Device collection with
Desktop/Tablet/Mobile modes.

It enforces **mode parity**: a collection must declare at least one mode, and *every* variable in
it must define a value for *every* mode — a variable that is themed in Light but forgotten in Dark
is rejected, exactly as the Design System enforced theme parity.

Pure domain: standard library, the shared-kernel error base, FD ids, the variable model, and
shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from figma_design.domain.shared.ids import VariableCollectionId
from figma_design.domain.shared.value_objects import CollectionKind
from figma_design.domain.variable.variable import Variable

__all__ = ["InvalidCollectionError", "VariableCollection"]


class InvalidCollectionError(DesignDirectorError):
    """Raised when a variable collection violates a structural invariant."""

    code = "invalid_figma_design_collection"
    http_status = 422


@dataclass(frozen=True, slots=True)
class VariableCollection:
    """A named set of variables sharing a set of modes.

    Attributes:
        id: Collection identity.
        kind: The role the collection plays (primitive / semantic / component / theme / device).
        name: A human-readable collection name.
        modes: The ordered mode names (e.g. ``("Light", "Dark")``); at least one, unique.
        variables: The variables, keyed by variable key. Every variable must value every mode.
    """

    id: VariableCollectionId
    kind: CollectionKind
    name: str
    modes: tuple[str, ...]
    variables: Mapping[str, Variable] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidCollectionError("VariableCollection.name must be non-empty.")
        modes = tuple(dict.fromkeys(m.strip() for m in self.modes if m and m.strip()))
        if not modes:
            raise InvalidCollectionError(
                "A VariableCollection must declare at least one mode.",
                details={"collection": self.name},
            )
        mode_set = set(modes)
        variables = dict(self.variables)
        for key, variable in variables.items():
            if variable.key != key:
                raise InvalidCollectionError(
                    "Variable key must match its map key.",
                    details={"map_key": key, "variable_key": variable.key},
                )
            if set(variable.modes) != mode_set:
                raise InvalidCollectionError(
                    "Mode parity violated: a variable must value exactly the collection's modes.",
                    details={
                        "collection": self.name,
                        "variable": variable.key,
                        "missing": sorted(mode_set - set(variable.modes)),
                        "extra": sorted(set(variable.modes) - mode_set),
                    },
                )
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "modes", modes)
        object.__setattr__(self, "variables", MappingProxyType(variables))

    @classmethod
    def of(
        cls,
        id: VariableCollectionId,
        kind: CollectionKind,
        name: str,
        modes: tuple[str, ...],
        variables: Iterable[Variable],
    ) -> VariableCollection:
        mapping: dict[str, Variable] = {}
        for variable in variables:
            if variable.key in mapping:
                raise InvalidCollectionError(
                    "Duplicate variable key in collection.", details={"key": variable.key}
                )
            mapping[variable.key] = variable
        return cls(id=id, kind=kind, name=name, modes=modes, variables=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.variables)

    def __iter__(self):
        return iter(self.variables.values())

    def has(self, key: str) -> bool:
        return key in self.variables

    def keys(self) -> tuple[str, ...]:
        return tuple(self.variables.keys())
