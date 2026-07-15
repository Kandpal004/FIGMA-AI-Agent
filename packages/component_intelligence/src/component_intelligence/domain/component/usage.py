"""UsageGuidance — the engine's WHEN, WHERE, and WHEN-NOT intelligence for a component.

A :class:`UsageGuidance` records where a component belongs (its page affinity), when it should
be used, when it should *not* be used, and which components it conflicts with. This is the
heart of the engine's intelligence — it does not merely list components, it knows the
conditions under which each earns or forfeits its place.

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from component_intelligence.domain.shared.ids import CIEvidenceId
from component_intelligence.domain.shared.value_objects import ComponentType, PageType

__all__ = ["UsageGuidance"]


@dataclass(frozen=True, slots=True)
class UsageGuidance:
    """Where and when a component should — and should not — be used.

    Attributes:
        page_affinity: The pages the component belongs on.
        when_to_use: The conditions under which the component earns its place.
        when_not_to_use: The conditions under which it should be omitted.
        conflicts_with: Components it cannot coexist with.
        evidence_ids: The evidence grounding the guidance.
    """

    page_affinity: tuple[PageType, ...] = ()
    when_to_use: tuple[str, ...] = ()
    when_not_to_use: tuple[str, ...] = ()
    conflicts_with: tuple[ComponentType, ...] = ()
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "page_affinity", tuple(dict.fromkeys(self.page_affinity)))
        object.__setattr__(self, "when_to_use", tuple(w for w in self.when_to_use if w and w.strip()))
        object.__setattr__(self, "when_not_to_use", tuple(w for w in self.when_not_to_use if w and w.strip()))
        object.__setattr__(self, "conflicts_with", tuple(dict.fromkeys(self.conflicts_with)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def belongs_on(self, page: PageType) -> bool:
        return page in self.page_affinity
