"""The design-token model — the three-tier core of the Design System Engine.

A :class:`DesignToken` is one named, cited design decision (a colour, a spacing step, a type
role, a radius, a shadow, a motion curve, …). Every token belongs to a :class:`TokenCategory`
and a :class:`TokenTier`:

* ``PRIMITIVE`` — a raw literal value (``#0A0A0A``, ``16``, ``1.25``). The only tier that holds
  literals.
* ``SEMANTIC`` — a role that *references* a primitive (``color.text.default`` → ``gray.900``).
* ``COMPONENT`` — a component-scoped role that references a semantic (``button.bg.default`` →
  ``color.action.primary``).

A :class:`TokenValue` is therefore either a literal *or* a reference (an alias) to another
token, never both. Aliases are resolved and cycle-checked by the token resolver
(application layer); the domain guarantees each individual value is well-formed and that the
tiering rule holds — a literal token must be ``PRIMITIVE``, a reference token must be
``SEMANTIC`` or ``COMPONENT``.

A :class:`TokenSet` is the immutable, unique-by-key registry of every token in a specification.

Pure domain: standard library, the shared-kernel error base, DS ids, evidence, and shared value
objects.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_system.domain.evidence.evidence import Citation
from design_system.domain.shared.ids import TokenId
from design_system.domain.shared.value_objects import Tag, TokenCategory, TokenTier

__all__ = [
    "DesignToken",
    "InvalidTokenError",
    "TokenNotFoundError",
    "TokenSet",
    "TokenValue",
]

# A dotted, lower-case token key: ``color.text.default``, ``space.4``, ``button.bg.hover``.
_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidTokenError(DesignDirectorError):
    """Raised when a token or token value is constructed with invalid data."""

    code = "invalid_design_system_token"
    http_status = 422


class TokenNotFoundError(DesignDirectorError):
    """Raised when a token is requested by a key absent from the set."""

    code = "design_system_token_not_found"
    http_status = 404


def _valid_key(key: str) -> str:
    normalized = key.strip().lower()
    if not _KEY.match(normalized):
        raise InvalidTokenError(
            "Token key must be dotted lower-case (e.g. 'color.text.default').",
            details={"key": key},
        )
    return normalized


@dataclass(frozen=True, slots=True)
class TokenValue:
    """A token's value: either a literal *or* a reference to another token — never both.

    Attributes:
        literal: The concrete value (e.g. ``"#0A0A0A"``, ``"16px"``, ``"1.25"``) when this is a
            primitive value. Mutually exclusive with ``ref``.
        ref: The key of the token this value aliases, when this is a reference. Mutually
            exclusive with ``literal``.
    """

    literal: str | None = None
    ref: str | None = None

    def __post_init__(self) -> None:
        has_literal = self.literal is not None
        has_ref = self.ref is not None
        if has_literal == has_ref:
            raise InvalidTokenError(
                "TokenValue must be exactly one of literal or ref.",
                details={"literal": self.literal, "ref": self.ref},
            )
        if has_literal:
            if not self.literal.strip():
                raise InvalidTokenError("TokenValue.literal must be non-empty.")
        else:
            object.__setattr__(self, "ref", _valid_key(self.ref))

    @property
    def is_reference(self) -> bool:
        return self.ref is not None

    @classmethod
    def of(cls, literal: str) -> TokenValue:
        """A literal value."""
        return cls(literal=literal)

    @classmethod
    def alias(cls, ref: str) -> TokenValue:
        """A reference to another token by key."""
        return cls(ref=ref)


@dataclass(frozen=True, slots=True)
class DesignToken:
    """One named, cited design decision within the three-tier token architecture.

    Attributes:
        id: Token identity within this specification.
        key: The dotted, lower-case token key (unique within the set).
        category: The token category (colour, spacing, typography, …).
        tier: The token tier (primitive / semantic / component).
        value: The literal value or the reference to another token.
        description: Human-readable intent.
        citations: The evidence supporting this token (must resolve in the evidence graph).
        tags: Free-form tags for filtering.
    """

    id: TokenId
    key: str
    category: TokenCategory
    tier: TokenTier
    value: TokenValue
    description: str = ""
    citations: tuple[Citation, ...] = ()
    tags: frozenset[Tag] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, "key", _valid_key(self.key))
        if self.value.is_reference:
            if self.tier is TokenTier.PRIMITIVE:
                raise InvalidTokenError(
                    "A primitive token must hold a literal, not a reference.",
                    details={"key": self.key},
                )
            if self.value.ref == self.key:
                raise InvalidTokenError(
                    "A token cannot reference itself.", details={"key": self.key}
                )
        elif self.tier is not TokenTier.PRIMITIVE:
            raise InvalidTokenError(
                "A literal token must be primitive; semantic/component tokens reference.",
                details={"key": self.key, "tier": self.tier.value},
            )
        object.__setattr__(self, "citations", tuple(self.citations))
        object.__setattr__(self, "tags", frozenset(self.tags))

    @property
    def is_reference(self) -> bool:
        return self.value.is_reference

    @property
    def evidence_ids(self) -> tuple:
        return tuple(c.evidence_id for c in self.citations)


@dataclass(frozen=True, slots=True)
class TokenSet:
    """The immutable, unique-by-key registry of every token in a specification."""

    items: Mapping[str, DesignToken] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def empty(cls) -> TokenSet:
        return cls()

    @classmethod
    def of(cls, tokens: Iterable[DesignToken]) -> TokenSet:
        """Build a set from tokens, keyed by their token key.

        Raises:
            InvalidTokenError: If two tokens share a key.
        """
        mapping: dict[str, DesignToken] = {}
        for token in tokens:
            if token.key in mapping:
                raise InvalidTokenError(
                    "Duplicate token key in set.", details={"key": token.key}
                )
            mapping[token.key] = token
        return cls(items=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def __contains__(self, key: str) -> bool:
        return key in self.items

    def has(self, key: str) -> bool:
        return key in self.items

    def get(self, key: str) -> DesignToken:
        """Return the token for ``key``.

        Raises:
            TokenNotFoundError: If no such token exists.
        """
        token = self.items.get(key)
        if token is None:
            raise TokenNotFoundError(f"Token {key!r} not found.", details={"key": key})
        return token

    def keys(self) -> tuple[str, ...]:
        return tuple(self.items.keys())

    def by_category(self, category: TokenCategory) -> tuple[DesignToken, ...]:
        return tuple(t for t in self.items.values() if t.category is category)

    def by_tier(self, tier: TokenTier) -> tuple[DesignToken, ...]:
        return tuple(t for t in self.items.values() if t.tier is tier)

    def references(self) -> tuple[DesignToken, ...]:
        """Every token whose value aliases another token."""
        return tuple(t for t in self.items.values() if t.is_reference)
