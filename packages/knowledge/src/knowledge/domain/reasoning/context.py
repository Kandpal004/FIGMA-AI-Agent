"""DecisionContext — the description of *what is being decided*.

A :class:`DecisionContext` is the input to the reasoning core: it names the design
question at hand — the categories of knowledge in play, the page and component
under design, the target platform, the goal, and any situational tags — so the
reasoner can select the applicable principles and assemble a cited rationale.

It is a pure, immutable value object with no I/O. The reasoner translates it into a
:class:`~knowledge.domain.reasoning.query.KnowledgeQuery` for structured retrieval
and then applies applicability matching.

Testing considerations
----------------------
* Iterables are normalized to frozensets; the value object is immutable.
* An empty context (no categories/facets) is valid and denotes "anything relevant".
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self

from knowledge.domain.shared.value_objects import Platform, Tag
from knowledge.domain.taxonomy.category import KnowledgeCategory

__all__ = ["DecisionContext"]


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """What is being decided, and under what conditions.

    Attributes:
        categories: Knowledge categories of interest (empty = any).
        page_type: The page under design, if any (e.g. ``"product"``).
        component_type: The component under design, if any (e.g. ``"buy_box"``).
        platform: The target commerce platform, if any.
        goal: A short free-text objective (e.g. "increase add-to-cart").
        contexts: Situational :class:`Tag` s (e.g. ``above-the-fold``).
        question: The natural-language question, if posed (used by future
            semantic discovery; ignored by structured matching).
    """

    categories: frozenset[KnowledgeCategory] = field(default_factory=frozenset)
    page_type: str | None = None
    component_type: str | None = None
    platform: Platform | None = None
    goal: str = ""
    contexts: frozenset[Tag] = field(default_factory=frozenset)
    question: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "categories", frozenset(self.categories))
        object.__setattr__(self, "contexts", frozenset(self.contexts))

    @classmethod
    def build(
        cls,
        *,
        categories: Iterable[KnowledgeCategory] = (),
        page_type: str | None = None,
        component_type: str | None = None,
        platform: Platform | None = None,
        goal: str = "",
        contexts: Iterable[Tag] = (),
        question: str = "",
    ) -> Self:
        """Ergonomic constructor accepting any iterables."""
        return cls(
            categories=frozenset(categories),
            page_type=page_type,
            component_type=component_type,
            platform=platform,
            goal=goal,
            contexts=frozenset(contexts),
            question=question,
        )
