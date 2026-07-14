"""Stage — Quality scoring.

Computes the report's calibrated quality picture deterministically:

* **coverage** — how many of the required outputs the architecture produced.
* **grounding** — the fraction of decisions whose citations resolve (``1.0`` by
  construction, surfaced here so the metric is auditable).
* **completeness** — the fraction of required pages that carry at least one required
  section.
* **confidence** — the aggregate confidence, anchored on how richly the pages are specified.
"""

from __future__ import annotations

from ia.application.contracts import IADraft
from ia.domain.graph.graphs import IAGraphs
from ia.domain.quality.quality import IAQualityMetrics
from ia.domain.shared.value_objects import Confidence, Percentage, RelationshipKind

__all__ = ["QualityScorer"]


class QualityScorer:
    """Scores the architecture's coverage, grounding, completeness, and confidence."""

    def score(self, draft: IADraft, graphs: IAGraphs) -> IAQualityMetrics:
        coverage = Percentage.ratio(*self._coverage(draft))
        grounding = Percentage.ratio(*self._grounding(draft, graphs))
        completeness = Percentage.ratio(*self._completeness(draft))
        return IAQualityMetrics(
            coverage=coverage,
            grounding=grounding,
            completeness=completeness,
            confidence=self._confidence(draft),
        )

    @staticmethod
    def _coverage(draft: IADraft) -> tuple[int, int]:
        sitemap = draft.sitemap
        nav = draft.navigation
        rel = draft.relationships
        disc = draft.discovery
        checklist = (
            bool(len(sitemap)),
            bool(sitemap.required()),
            bool(sitemap.optional()),
            bool(nav.global_nav.items),
            bool(nav.footer.columns),
            nav.breadcrumbs.enabled,
            bool(len(rel)),
            bool(rel.by_kind(RelationshipKind.CROSS_SELL) or rel.by_kind(RelationshipKind.RELATED)),
            bool(rel.internal_linking.principles),
            bool(disc.search.scope),
            bool(disc.filtering.facets),
            bool(disc.sorting.options),
        )
        return sum(1 for present in checklist if present), len(checklist)

    @staticmethod
    def _grounding(draft: IADraft, graphs: IAGraphs) -> tuple[int, int]:
        # Grounding over the citable leaf decisions: pages, sections, nav items,
        # relationships, and graph nodes.
        citable: list[tuple[object, tuple]] = []
        for page in draft.sitemap:
            citable.append((page, page.all_evidence_ids()))
            for section in (*page.required_sections, *page.optional_sections):
                citable.append((section, section.all_evidence_ids()))
        for item in draft.navigation.all_items():
            citable.append((item, item.all_evidence_ids()))
        for rel in draft.relationships:
            citable.append((rel, rel.evidence_ids))
        for graph in graphs.all():
            for node in graph:
                citable.append((node, node.evidence_ids))
        if not citable:
            return 0, 1
        grounded = sum(1 for _, ev in citable if ev)
        return grounded, len(citable)

    @staticmethod
    def _completeness(draft: IADraft) -> tuple[int, int]:
        required = draft.sitemap.required()
        if not required:
            return 0, 1
        with_section = sum(1 for p in required if p.required_sections)
        return with_section, len(required)

    @staticmethod
    def _confidence(draft: IADraft) -> Confidence:
        pages = tuple(draft.sitemap)
        if not pages:
            return Confidence.of(0.0)
        detailed = sum(1 for p in pages if p.required_sections and p.primary_actions)
        return Confidence.clamp(0.5 + 0.5 * (detailed / len(pages)))
