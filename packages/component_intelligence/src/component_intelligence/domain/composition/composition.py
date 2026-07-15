"""The ComponentComposition — the intelligently-selected set of component decisions.

A :class:`ComponentComposition` is the immutable set of :class:`ComponentDecision` s the engine
produces, one per component it reasoned about (included, optional, or excluded). It is the
authoritative answer to "which components should exist" — every one carrying the intelligence
for *why*.

Pure domain: standard library, the shared-kernel error base, CI ids, and the decision model.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.component.decision import ComponentDecision
from component_intelligence.domain.shared.ids import CIEvidenceId
from component_intelligence.domain.shared.value_objects import ComponentType, PageType

__all__ = ["ComponentComposition", "InvalidCompositionError"]


class InvalidCompositionError(DesignDirectorError):
    """Raised when a composition is constructed with invalid data (duplicate component)."""

    code = "invalid_component_intelligence_composition"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ComponentComposition:
    """The set of component decisions that constitute the composition."""

    decisions: tuple[ComponentDecision, ...] = ()

    def __post_init__(self) -> None:
        seen: set[ComponentType] = set()
        for decision in self.decisions:
            if decision.component in seen:
                raise InvalidCompositionError(
                    "Duplicate component decision.", details={"component": decision.component.value}
                )
            seen.add(decision.component)
        object.__setattr__(self, "decisions", tuple(self.decisions))

    @classmethod
    def of(cls, decisions: Iterable[ComponentDecision]) -> ComponentComposition:
        return cls(decisions=tuple(decisions))

    def __len__(self) -> int:
        return len(self.decisions)

    def __iter__(self):
        return iter(self.decisions)

    def included(self) -> tuple[ComponentDecision, ...]:
        return tuple(d for d in self.decisions if d.is_included)

    def get(self, component: ComponentType) -> ComponentDecision | None:
        return next((d for d in self.decisions if d.component is component), None)

    def has(self, component: ComponentType) -> bool:
        return any(d.component is component for d in self.decisions)

    def components(self) -> frozenset[ComponentType]:
        return frozenset(d.component for d in self.decisions)

    def included_components(self) -> frozenset[ComponentType]:
        return frozenset(d.component for d in self.included())

    def on_page(self, page: PageType) -> tuple[ComponentDecision, ...]:
        """The included components that belong on a page (by affinity)."""
        return tuple(d for d in self.included() if d.belongs_on(page))

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for d in self.decisions for eid in d.all_evidence_ids())
