"""Serializable view DTOs — the read models the inbound layer returns.

Callers receive these flat, primitive-typed projections of an :class:`IAReport` (or a
:class:`WireframeBriefBundle`) — never the domain aggregate. Pure data with ``from_*``
builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ia.domain.graph.ia_graph import IAGraph
from ia.domain.navigation.nav_item import NavItem
from ia.domain.navigation.navigation import Navigation
from ia.domain.page.page_blueprint import PageBlueprint
from ia.domain.report.bundle import WireframeBriefBundle
from ia.domain.report.report import IAReport

__all__ = [
    "GraphView",
    "IATraceView",
    "NavigationView",
    "PageView",
    "QualityView",
    "ReportView",
    "WireframeBriefBundleView",
]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _iso(value) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _section_view(s) -> dict:
    return {
        "type": s.type.value, "purpose": s.purpose, "priority": int(s.priority),
        "placement": s.placement.value, "is_required": s.is_required,
        "content_blocks": [{"kind": b.kind.value, "label": b.label, "priority": int(b.priority)}
                           for b in s.blocks_by_priority()],
        "evidence_ids": _ids(s.all_evidence_ids()),
    }


def _page_view(p: PageBlueprint) -> dict:
    return {
        "id": str(p.id), "page_type": p.page_type.value, "requirement": p.requirement.value,
        "purpose": p.purpose, "slug_intent": p.slug_intent,
        "goals": {"business": p.goals.business_goal, "primary_user": p.goals.primary_user_goal,
                  "secondary_user": p.goals.secondary_user_goal},
        "required_sections": [_section_view(s) for s in p.required_sections],
        "optional_sections": [_section_view(s) for s in p.optional_sections],
        "priorities": {"navigation": int(p.priorities.navigation), "seo": int(p.priorities.seo),
                       "accessibility": int(p.priorities.accessibility),
                       "conversion": int(p.priorities.conversion), "mobile": int(p.priorities.mobile),
                       "overall": p.priorities.overall},
        "primary_actions": [{"action": a.action, "target": (a.target.value if a.target else None),
                             "placement": a.placement.value} for a in p.primary_actions],
        "secondary_actions": [a.action for a in p.secondary_actions],
        "trust_placement": p.trust_placement.value, "conversion_placement": p.conversion_placement.value,
        "evidence_ids": _ids(p.all_evidence_ids()),
    }


def _nav_item_view(i: NavItem) -> dict:
    return {
        "label_intent": i.label_intent, "target": (i.target.value if i.target else None),
        "children": [_nav_item_view(c) for c in i.children],
    }


def _navigation_view(n: Navigation) -> dict:
    return {
        "global": [_nav_item_view(i) for i in n.global_nav.items],
        "mega_menu": {"enabled": n.mega_menu.enabled, "columns": [_nav_item_view(i) for i in n.mega_menu.columns]},
        "footer": [_nav_item_view(i) for i in n.footer.columns],
        "breadcrumbs": {"enabled": n.breadcrumbs.enabled, "strategy": n.breadcrumbs.strategy,
                        "shown_on": [p.value for p in n.breadcrumbs.shown_on]},
        "utility": [_nav_item_view(i) for i in n.utility],
    }


def _graph_view(g: IAGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(x.id), "kind": x.kind.value, "label": x.label, "evidence_ids": _ids(x.evidence_ids)}
                  for x in g],
        "edges": [{"source": str(e.source), "target": str(e.target), "relation": e.relation.value}
                  for e in g.edges],
    }


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    coverage: float
    grounding: float
    completeness: float
    confidence: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class PageView:
    page: dict


@dataclass(frozen=True, slots=True)
class NavigationView:
    navigation: dict


@dataclass(frozen=True, slots=True)
class GraphView:
    graph: dict


@dataclass(frozen=True, slots=True)
class ReportView:
    """The full, flat projection of an information architecture report."""

    report_id: str
    lineage_id: str
    version: int
    project_id: str
    is_usable: bool
    created_at: str
    quality: QualityView
    required_pages: list[dict]
    optional_pages: list[dict]
    navigation: dict
    relationships: list[dict]
    internal_linking: dict
    discovery: dict
    graphs: dict
    evidence_count: int

    @classmethod
    def from_report(cls, r: IAReport) -> ReportView:
        quality = QualityView(
            overall_score=r.quality.overall_score.value, band=r.quality.band.value,
            coverage=r.quality.coverage.value, grounding=r.quality.grounding.value,
            completeness=r.quality.completeness.value, confidence=r.quality.confidence.value,
            is_fully_grounded=r.quality.is_fully_grounded,
        )
        d = r.discovery
        discovery = {
            "search": {"scope": d.search.scope, "autocomplete": d.search.autocomplete,
                       "no_results_handling": d.search.no_results_handling},
            "filtering": {"facets": [f.value for f in d.filtering.facets]},
            "sorting": {"options": [o.value for o in d.sorting.options], "default": d.sorting.default.value},
        }
        return cls(
            report_id=str(r.id), lineage_id=str(r.lineage_id), version=r.version,
            project_id=r.project_id, is_usable=r.is_usable, created_at=_iso(r.created_at),
            quality=quality,
            required_pages=[_page_view(p) for p in r.sitemap.required()],
            optional_pages=[_page_view(p) for p in r.sitemap.optional()],
            navigation=_navigation_view(r.navigation),
            relationships=[
                {"source": rel.source.value, "target": rel.target.value, "kind": rel.kind.value,
                 "rationale": rel.rationale, "evidence_ids": _ids(rel.evidence_ids)}
                for rel in r.relationships
            ],
            internal_linking={"principles": list(r.relationships.internal_linking.principles),
                              "hub_pages": [p.value for p in r.relationships.internal_linking.hub_pages]},
            discovery=discovery,
            graphs={g.kind.value: _graph_view(g) for g in r.graphs.all()},
            evidence_count=r.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class WireframeBriefBundleView:
    """The neutral wireframe brief downstream design phases consume."""

    report_id: str
    project_id: str
    pages: list[dict]
    navigation: dict
    relationships: list[dict]
    discovery: dict
    is_usable: bool
    created_at: str

    @classmethod
    def from_bundle(cls, b: WireframeBriefBundle) -> WireframeBriefBundleView:
        d = b.discovery
        return cls(
            report_id=str(b.report_id), project_id=b.project_id,
            pages=[_page_view(p) for p in b.pages],
            navigation=_navigation_view(b.navigation),
            relationships=[
                {"source": rel.source.value, "target": rel.target.value, "kind": rel.kind.value}
                for rel in b.relationships
            ],
            discovery={
                "search": {"scope": d.search.scope},
                "filtering": {"facets": [f.value for f in d.filtering.facets]},
                "sorting": {"options": [o.value for o in d.sorting.options], "default": d.sorting.default.value},
            },
            is_usable=b.is_usable, created_at=_iso(b.created_at),
        )


@dataclass(frozen=True, slots=True)
class IATraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
