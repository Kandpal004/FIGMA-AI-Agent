"""Stage — Coherence Resolution.

The brain proposes components independently; this stage makes the composition *coherent* — the
WHEN-NOT logic. It resolves conflicts (when two included components cannot coexist, it keeps the
higher-priority, higher-converting one and excludes the other) and closes dependencies (a
component that an included component needs is itself promoted to included). The result is a
composition the aggregate's coherence invariant will accept: no conflicting pair both included,
every dependency satisfied.

The resolution is deterministic: conflict losers are chosen by (priority, conversion effect),
with a lexicographic tie-break, so the same draft always resolves the same way.
"""

from __future__ import annotations

from dataclasses import replace

from component_intelligence.application.contracts import CompositionDraft
from component_intelligence.domain.component.decision import ComponentDecision
from component_intelligence.domain.composition.composition import ComponentComposition
from component_intelligence.domain.shared.value_objects import ComponentType, EffectLevel, Inclusion

__all__ = ["CoherenceResolver"]

_EFFECT_RANK = {
    EffectLevel.STRONG: 3, EffectLevel.MODERATE: 2, EffectLevel.SLIGHT: 1, EffectLevel.NONE: 0,
}


class CoherenceResolver:
    """Resolves conflicts and closes dependencies into a coherent composition."""

    def resolve(self, draft: CompositionDraft) -> ComponentComposition:
        decisions: dict[ComponentType, ComponentDecision] = {
            d.component: d for d in draft.composition
        }
        order = [d.component for d in draft.composition]
        conflict_pairs = self._conflict_pairs(draft)

        # 1. Resolve conflicts — exclude the loser of each included conflicting pair.
        losers: set[ComponentType] = set()
        for a, b in conflict_pairs:
            da, db = decisions.get(a), decisions.get(b)
            if (
                da is not None and db is not None
                and da.is_included and db.is_included
                and a not in losers and b not in losers
            ):
                losers.add(self._loser(da, db))
        for component in losers:
            decisions[component] = replace(decisions[component], inclusion=Inclusion.EXCLUDED)

        # 2. Close dependencies — promote every needed-but-not-included component.
        changed = True
        while changed:
            changed = False
            included = {c for c, d in decisions.items() if d.is_included}
            for component in list(included):
                decision = decisions[component]
                needs = set(decision.dependencies) | set(
                    draft.compatibility.requires_of(component)
                )
                for need in needs:
                    nd = decisions.get(need)
                    if nd is not None and not nd.is_included and need not in losers:
                        decisions[need] = replace(nd, inclusion=Inclusion.INCLUDED)
                        changed = True

        return ComponentComposition.of(decisions[c] for c in order)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _conflict_pairs(draft: CompositionDraft) -> list[tuple[ComponentType, ComponentType]]:
        pairs: set[frozenset[ComponentType]] = set()
        for link in draft.compatibility.conflicts():
            pairs.add(frozenset({link.source, link.target}))
        for decision in draft.composition:
            for other in decision.usage.conflicts_with:
                if decision.component is not other:
                    pairs.add(frozenset({decision.component, other}))
        return [tuple(sorted(p, key=lambda c: c.value)) for p in pairs]  # type: ignore[misc]

    @staticmethod
    def _loser(a: ComponentDecision, b: ComponentDecision) -> ComponentType:
        ka = (int(a.priority), _EFFECT_RANK[a.impacts.conversion_effect])
        kb = (int(b.priority), _EFFECT_RANK[b.impacts.conversion_effect])
        if ka < kb:
            return a.component
        if kb < ka:
            return b.component
        # Deterministic tie-break: exclude the lexicographically greater component.
        return a.component if a.component.value > b.component.value else b.component
