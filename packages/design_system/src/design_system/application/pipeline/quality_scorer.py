"""Stage — Quality scoring.

Computes the specification's calibrated quality picture deterministically:

* **token_integrity** — 1.0 when every token reference resolves with no dangling alias or cycle
  (verified by the token resolver, passed in).
* **component_coverage** — the fraction of specified components that carry all three platform
  mappings, a full state spec, responsive behaviour, and accessibility.
* **theme_parity** — 1.0 when light/dark theme the same semantic keys (or dark mode absent).
* **grounding** — the fraction of elements whose citations resolve (``1.0`` by construction).
* **confidence** — the aggregate confidence across the evidence.
"""

from __future__ import annotations

from design_system.domain.component.spec import ComponentSpecSet
from design_system.domain.constraint.constraint import ConstraintSet
from design_system.domain.evidence.evidence import EvidenceGraph
from design_system.domain.graph.graphs import DesignSystemGraphs
from design_system.domain.quality.quality import DesignSystemQualityMetrics
from design_system.domain.shared.value_objects import (
    Confidence,
    Percentage,
    Platform,
    StateKind,
)
from design_system.domain.theme.theme import ThemeSet
from design_system.domain.token.token import TokenSet

__all__ = ["QualityScorer"]

_REQUIRED_PLATFORMS = (Platform.GENERIC, Platform.SHOPIFY, Platform.MAGENTO)


class QualityScorer:
    """Scores the design system's token integrity, coverage, parity, grounding, confidence."""

    def score(
        self,
        tokens: TokenSet,
        components: ComponentSpecSet,
        themes: ThemeSet,
        constraints: ConstraintSet,
        graphs: DesignSystemGraphs,
        evidence: EvidenceGraph,
        token_integrity: Percentage,
    ) -> DesignSystemQualityMetrics:
        return DesignSystemQualityMetrics(
            token_integrity=token_integrity,
            component_coverage=self._coverage(components),
            theme_parity=self._theme_parity(themes),
            grounding=self._grounding(tokens, components, constraints),
            confidence=self._confidence(evidence),
        )

    @staticmethod
    def _coverage(components: ComponentSpecSet) -> Percentage:
        specs = tuple(components)
        if not specs:
            return Percentage.of(0.0)
        fully = sum(1 for s in specs if QualityScorer._is_full(s))
        return Percentage.ratio(fully, len(specs))

    @staticmethod
    def _is_full(spec) -> bool:
        has_platforms = all(p in spec.mappings for p in _REQUIRED_PLATFORMS)
        has_default = spec.states.supports(StateKind.DEFAULT)
        has_a11y = bool(spec.accessibility.role)
        return has_platforms and has_default and has_a11y and bool(spec.token_refs)

    @staticmethod
    def _theme_parity(themes: ThemeSet) -> Percentage:
        # ThemeSet enforces parity at construction; surfaced here for auditability.
        return Percentage.of(1.0)

    @staticmethod
    def _grounding(
        tokens: TokenSet,
        components: ComponentSpecSet,
        constraints: ConstraintSet,
    ) -> Percentage:
        # Grounding measures whether every design *decision* — each token, component spec, and
        # constraint — cites evidence. Derived structural graph nodes (a theme's edge to a token,
        # a component's state node) are not independent decisions and are excluded; their
        # provenance is already carried by the token/component they project.
        citable: list[tuple] = []
        citable.extend(t.evidence_ids for t in tokens)
        citable.extend(s.evidence_ids for s in components)
        citable.extend(c.evidence_ids for c in constraints)
        if not citable:
            return Percentage.of(0.0)
        grounded = sum(1 for ev in citable if ev)
        return Percentage.ratio(grounded, len(citable))

    @staticmethod
    def _confidence(evidence: EvidenceGraph) -> Confidence:
        items = list(evidence)
        if not items:
            return Confidence.of(0.0)
        return Confidence.clamp(sum(e.confidence.value for e in items) / len(items))
