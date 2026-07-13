"""Applicability — the structured predicate that powers deterministic relevance.

This is what lets the engine answer *"which accessibility rule applies to **this**
button?"* without guessing. An :class:`Applicability` declares the situations an
entry applies to along four independent facets — page types, component types,
platforms, and contextual tags. An empty facet means "applies to any", so a facet
constrains only when populated.

Matching is a pure, deterministic predicate over primitive arguments (not a
``DecisionContext`` — that keeps this module free of any dependency on the
reasoning layer, so the dependency graph stays acyclic). :meth:`Applicability.matches`
answers *does this apply here?*; :meth:`Applicability.specificity` answers *how
tightly?*, which the reasoner uses to rank a more specific rule above a general one.

Pure domain: standard library, shared-kernel error base, and the platform enum.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self

from core.errors import DesignDirectorError

from knowledge.domain.shared.value_objects import Platform, Tag

__all__ = ["Applicability", "InvalidApplicabilityError"]


class InvalidApplicabilityError(DesignDirectorError):
    """Raised when an applicability predicate is constructed with invalid data."""

    code = "invalid_applicability"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Applicability:
    """The situations a knowledge entry applies to.

    Each facet is a set; an empty facet does not constrain (matches anything). A
    non-empty facet matches only when the queried value is a member (and, for a
    value the caller left unspecified, that facet does not filter).

    Attributes:
        page_types: Page slugs the entry applies to (e.g. ``{"product", "cart"}``).
        component_types: Component slugs (e.g. ``{"button", "form"}``).
        platforms: Platforms; :data:`Platform.AGNOSTIC` matches any platform.
        contexts: Situational :class:`Tag` s (e.g. ``above-the-fold``).
    """

    page_types: frozenset[str] = field(default_factory=frozenset)
    component_types: frozenset[str] = field(default_factory=frozenset)
    platforms: frozenset[Platform] = field(default_factory=frozenset)
    contexts: frozenset[Tag] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        # Normalise any iterable into a frozenset for immutability + hashing.
        object.__setattr__(self, "page_types", frozenset(self.page_types))
        object.__setattr__(self, "component_types", frozenset(self.component_types))
        object.__setattr__(self, "platforms", frozenset(self.platforms))
        object.__setattr__(self, "contexts", frozenset(self.contexts))

    @classmethod
    def any(cls) -> Self:
        """An applicability that matches everything (no facet constrained)."""
        return cls()

    @classmethod
    def build(
        cls,
        *,
        page_types: Iterable[str] = (),
        component_types: Iterable[str] = (),
        platforms: Iterable[Platform] = (),
        contexts: Iterable[Tag] = (),
    ) -> Self:
        """Ergonomic constructor accepting any iterables."""
        return cls(
            page_types=frozenset(page_types),
            component_types=frozenset(component_types),
            platforms=frozenset(platforms),
            contexts=frozenset(contexts),
        )

    @property
    def is_universal(self) -> bool:
        """Whether no facet is constrained (applies everywhere)."""
        return not (self.page_types or self.component_types or self.platforms or self.contexts)

    def specificity(self) -> int:
        """How tightly scoped this predicate is — the number of constrained facets
        plus the count of contextual tags. Higher means more specific, which the
        reasoner ranks above more general knowledge."""
        score = 0
        score += 1 if self.page_types else 0
        score += 1 if self.component_types else 0
        score += 1 if self.platforms else 0
        score += len(self.contexts)
        return score

    def matches(
        self,
        *,
        page_type: str | None = None,
        component_type: str | None = None,
        platform: Platform | None = None,
        contexts: Iterable[Tag] = (),
    ) -> bool:
        """Whether this applies to the described situation.

        A constrained facet fails the match only when the caller *supplies* a
        value for it that is not covered. Unspecified caller values never cause a
        failure — absence of information is not evidence of non-applicability.
        """
        if self.page_types and page_type is not None and page_type not in self.page_types:
            return False
        if (
            self.component_types
            and component_type is not None
            and component_type not in self.component_types
        ):
            return False
        if self.platforms and platform is not None:
            if platform not in self.platforms and Platform.AGNOSTIC not in self.platforms:
                return False
        if self.contexts:
            supplied = frozenset(contexts)
            if supplied and self.contexts.isdisjoint(supplied):
                return False
        return True
