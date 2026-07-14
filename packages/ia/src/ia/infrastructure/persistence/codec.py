"""Codec — serializes an IAReport to a JSON document and back.

A report is a deep, immutable aggregate; it is stored and loaded whole as one JSON document.
This codec is the single, exhaustive translation. Reconstruction goes through the normal
aggregate constructor, so a decoded report is re-validated (its provenance and structural
integrity re-checked, its graphs and content tree re-checked for acyclicity) — a corrupt
document cannot yield an invalid or ungrounded architecture.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from ia.domain.discovery.discovery import (
    Discovery,
    FilteringStrategy,
    SearchStrategy,
    SortingStrategy,
)
from ia.domain.evidence.evidence import EvidenceGraph, IAEvidence
from ia.domain.graph.graphs import IAGraphs
from ia.domain.graph.ia_graph import IAEdge, IAGraph, IANode
from ia.domain.navigation.nav_item import NavItem
from ia.domain.navigation.navigation import (
    Breadcrumbs,
    Footer,
    GlobalNavigation,
    MegaMenu,
    Navigation,
)
from ia.domain.page.action import PageAction
from ia.domain.page.goals import PageGoals
from ia.domain.page.page_blueprint import PageBlueprint
from ia.domain.page.priorities import PagePriorities
from ia.domain.quality.quality import IAQualityMetrics
from ia.domain.relationship.relationship import (
    InternalLinkingStrategy,
    PageRelationship,
    RelationshipSet,
)
from ia.domain.report.report import IAReport
from ia.domain.section.section import ContentBlock, Section
from ia.domain.shared.ids import (
    ContentBlockId,
    IAEdgeId,
    IAEvidenceId,
    IANodeId,
    IAReportId,
    IAReportLineageId,
    NavItemId,
    PageActionId,
    PageBlueprintId,
    PageRelationshipId,
    SectionId,
)
from ia.domain.shared.value_objects import (
    ActionType,
    Confidence,
    ContentBlockKind,
    FilterType,
    GraphKind,
    GraphRelation,
    NodeKind,
    PageRequirement,
    PageType,
    Percentage,
    Placement,
    Priority,
    ProvenanceKind,
    RelationshipKind,
    SectionType,
    SortOption,
    Tag,
)
from ia.domain.sitemap.sitemap import SiteMap

__all__ = ["from_document", "to_document"]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _eids(raw) -> tuple[IAEvidenceId, ...]:
    return tuple(IAEvidenceId.from_string(x) for x in raw)


# --------------------------- serialize ---------------------------------- #
def to_document(r: IAReport) -> dict:
    return {
        "id": str(r.id),
        "lineage_id": str(r.lineage_id),
        "version": r.version,
        "project_id": r.project_id,
        "created_at": r.created_at.isoformat(),
        "quality": {
            "coverage": r.quality.coverage.value, "grounding": r.quality.grounding.value,
            "completeness": r.quality.completeness.value, "confidence": r.quality.confidence.value,
        },
        "evidence": [
            {"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
             "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
             "source_name": e.source_name, "tags": [t.value for t in e.tags]}
            for e in r.evidence_graph
        ],
        "sitemap": [_page_doc(p) for p in r.sitemap],
        "navigation": _navigation_doc(r.navigation),
        "relationships": {
            "items": [
                {"id": str(x.id), "source": x.source.value, "target": x.target.value,
                 "kind": x.kind.value, "rationale": x.rationale, "evidence_ids": _ids(x.evidence_ids)}
                for x in r.relationships
            ],
            "internal_linking": {
                "principles": list(r.relationships.internal_linking.principles),
                "hub_pages": [p.value for p in r.relationships.internal_linking.hub_pages],
                "evidence_ids": _ids(r.relationships.internal_linking.evidence_ids),
            },
        },
        "discovery": _discovery_doc(r.discovery),
        "graphs": {g.kind.value: _graph_doc(g) for g in r.graphs.all()},
    }


def _block_doc(b: ContentBlock) -> dict:
    return {"id": str(b.id), "kind": b.kind.value, "label": b.label, "priority": int(b.priority),
            "evidence_ids": _ids(b.evidence_ids)}


def _section_doc(s: Section) -> dict:
    return {
        "id": str(s.id), "type": s.type.value, "purpose": s.purpose, "priority": int(s.priority),
        "placement": s.placement.value, "is_required": s.is_required,
        "content_blocks": [_block_doc(b) for b in s.content_blocks], "evidence_ids": _ids(s.evidence_ids),
    }


def _page_doc(p: PageBlueprint) -> dict:
    return {
        "id": str(p.id), "page_type": p.page_type.value, "requirement": p.requirement.value,
        "purpose": p.purpose, "slug_intent": p.slug_intent,
        "goals": {"business_goal": p.goals.business_goal, "primary_user_goal": p.goals.primary_user_goal,
                  "secondary_user_goal": p.goals.secondary_user_goal, "evidence_ids": _ids(p.goals.evidence_ids)},
        "required_sections": [_section_doc(s) for s in p.required_sections],
        "optional_sections": [_section_doc(s) for s in p.optional_sections],
        "priorities": {"navigation": int(p.priorities.navigation), "seo": int(p.priorities.seo),
                       "accessibility": int(p.priorities.accessibility),
                       "conversion": int(p.priorities.conversion), "mobile": int(p.priorities.mobile)},
        "primary_actions": [_action_doc(a) for a in p.primary_actions],
        "secondary_actions": [_action_doc(a) for a in p.secondary_actions],
        "trust_placement": p.trust_placement.value, "conversion_placement": p.conversion_placement.value,
        "evidence_ids": _ids(p.evidence_ids),
    }


def _action_doc(a: PageAction) -> dict:
    return {"id": str(a.id), "type": a.type.value, "action": a.action,
            "target": (a.target.value if a.target else None), "placement": a.placement.value,
            "evidence_ids": _ids(a.evidence_ids)}


def _nav_item_doc(i: NavItem) -> dict:
    return {"id": str(i.id), "label_intent": i.label_intent,
            "target": (i.target.value if i.target else None),
            "children": [_nav_item_doc(c) for c in i.children], "evidence_ids": _ids(i.evidence_ids)}


def _navigation_doc(n: Navigation) -> dict:
    return {
        "global_nav": {"items": [_nav_item_doc(i) for i in n.global_nav.items],
                       "principles": list(n.global_nav.principles), "evidence_ids": _ids(n.global_nav.evidence_ids)},
        "mega_menu": {"enabled": n.mega_menu.enabled, "columns": [_nav_item_doc(i) for i in n.mega_menu.columns],
                      "evidence_ids": _ids(n.mega_menu.evidence_ids)},
        "footer": {"columns": [_nav_item_doc(i) for i in n.footer.columns], "evidence_ids": _ids(n.footer.evidence_ids)},
        "breadcrumbs": {"enabled": n.breadcrumbs.enabled, "strategy": n.breadcrumbs.strategy,
                        "shown_on": [p.value for p in n.breadcrumbs.shown_on],
                        "evidence_ids": _ids(n.breadcrumbs.evidence_ids)},
        "utility": [_nav_item_doc(i) for i in n.utility],
    }


def _discovery_doc(d: Discovery) -> dict:
    return {
        "search": {"scope": d.search.scope, "autocomplete": d.search.autocomplete,
                   "no_results_handling": d.search.no_results_handling, "principles": list(d.search.principles),
                   "evidence_ids": _ids(d.search.evidence_ids)},
        "filtering": {"facets": [f.value for f in d.filtering.facets], "principles": list(d.filtering.principles),
                      "evidence_ids": _ids(d.filtering.evidence_ids)},
        "sorting": {"options": [o.value for o in d.sorting.options], "default": d.sorting.default.value,
                    "evidence_ids": _ids(d.sorting.evidence_ids)},
    }


def _graph_doc(g: IAGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                   "relation": e.relation.value} for e in g.edges],
    }


# --------------------------- deserialize -------------------------------- #
def from_document(doc: dict) -> IAReport:
    evidence_graph = EvidenceGraph.of(
        IAEvidence(
            id=IAEvidenceId.from_string(e["id"]), provenance=ProvenanceKind(e["provenance"]),
            external_ref=e["external_ref"], claim=e["claim"], confidence=Confidence.of(e["confidence"]),
            statement=e.get("statement", ""), source_name=e.get("source_name", ""),
            tags=frozenset(Tag.of(t) for t in e.get("tags", ())),
        )
        for e in doc["evidence"]
    )
    quality = IAQualityMetrics(
        coverage=Percentage.of(doc["quality"]["coverage"]),
        grounding=Percentage.of(doc["quality"]["grounding"]),
        completeness=Percentage.of(doc["quality"]["completeness"]),
        confidence=Confidence.of(doc["quality"]["confidence"]),
    )
    return IAReport(
        id=IAReportId.from_string(doc["id"]),
        lineage_id=IAReportLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], project_id=doc["project_id"],
        sitemap=SiteMap.of(_page(p) for p in doc["sitemap"]),
        navigation=_navigation(doc["navigation"]),
        relationships=_relationships(doc["relationships"]),
        discovery=_discovery(doc["discovery"]),
        graphs=_graphs(doc["graphs"]),
        evidence_graph=evidence_graph, quality=quality,
        created_at=datetime.fromisoformat(doc["created_at"]),
    )


def _block(doc: dict) -> ContentBlock:
    return ContentBlock(id=ContentBlockId.from_string(doc["id"]), kind=ContentBlockKind(doc["kind"]),
                        label=doc["label"], priority=Priority(doc["priority"]), evidence_ids=_eids(doc["evidence_ids"]))


def _section(doc: dict) -> Section:
    return Section(
        id=SectionId.from_string(doc["id"]), type=SectionType(doc["type"]), purpose=doc["purpose"],
        priority=Priority(doc["priority"]), placement=Placement(doc["placement"]),
        is_required=doc["is_required"],
        content_blocks=tuple(_block(b) for b in doc["content_blocks"]), evidence_ids=_eids(doc["evidence_ids"]),
    )


def _action(doc: dict) -> PageAction:
    return PageAction(id=PageActionId.from_string(doc["id"]), type=ActionType(doc["type"]),
                      action=doc["action"], target=PageType(doc["target"]) if doc.get("target") else None,
                      placement=Placement(doc["placement"]), evidence_ids=_eids(doc["evidence_ids"]))


def _page(doc: dict) -> PageBlueprint:
    g = doc["goals"]
    pr = doc["priorities"]
    return PageBlueprint(
        id=PageBlueprintId.from_string(doc["id"]), page_type=PageType(doc["page_type"]),
        requirement=PageRequirement(doc["requirement"]), purpose=doc["purpose"],
        slug_intent=doc.get("slug_intent", ""),
        goals=PageGoals(business_goal=g["business_goal"], primary_user_goal=g["primary_user_goal"],
                        secondary_user_goal=g.get("secondary_user_goal", ""), evidence_ids=_eids(g["evidence_ids"])),
        required_sections=tuple(_section(s) for s in doc["required_sections"]),
        optional_sections=tuple(_section(s) for s in doc["optional_sections"]),
        priorities=PagePriorities(navigation=Priority(pr["navigation"]), seo=Priority(pr["seo"]),
                                  accessibility=Priority(pr["accessibility"]), conversion=Priority(pr["conversion"]),
                                  mobile=Priority(pr["mobile"])),
        primary_actions=tuple(_action(a) for a in doc["primary_actions"]),
        secondary_actions=tuple(_action(a) for a in doc["secondary_actions"]),
        trust_placement=Placement(doc["trust_placement"]), conversion_placement=Placement(doc["conversion_placement"]),
        evidence_ids=_eids(doc["evidence_ids"]),
    )


def _nav_item(doc: dict) -> NavItem:
    return NavItem(
        id=NavItemId.from_string(doc["id"]), label_intent=doc["label_intent"],
        target=PageType(doc["target"]) if doc.get("target") else None,
        children=tuple(_nav_item(c) for c in doc.get("children", ())), evidence_ids=_eids(doc["evidence_ids"]),
    )


def _navigation(doc: dict) -> Navigation:
    gn, mm, ft, bc = doc["global_nav"], doc["mega_menu"], doc["footer"], doc["breadcrumbs"]
    return Navigation(
        global_nav=GlobalNavigation(items=tuple(_nav_item(i) for i in gn["items"]),
                                    principles=tuple(gn.get("principles", ())), evidence_ids=_eids(gn["evidence_ids"])),
        mega_menu=MegaMenu(enabled=mm["enabled"], columns=tuple(_nav_item(i) for i in mm["columns"]),
                           evidence_ids=_eids(mm["evidence_ids"])),
        footer=Footer(columns=tuple(_nav_item(i) for i in ft["columns"]), evidence_ids=_eids(ft["evidence_ids"])),
        breadcrumbs=Breadcrumbs(enabled=bc["enabled"], strategy=bc.get("strategy", ""),
                                shown_on=tuple(PageType(p) for p in bc.get("shown_on", ())),
                                evidence_ids=_eids(bc["evidence_ids"])),
        utility=tuple(_nav_item(i) for i in doc.get("utility", ())),
    )


def _relationships(doc: dict) -> RelationshipSet:
    il = doc["internal_linking"]
    return RelationshipSet.of(
        (
            PageRelationship(id=PageRelationshipId.from_string(x["id"]), source=PageType(x["source"]),
                             target=PageType(x["target"]), kind=RelationshipKind(x["kind"]),
                             rationale=x.get("rationale", ""), evidence_ids=_eids(x["evidence_ids"]))
            for x in doc["items"]
        ),
        InternalLinkingStrategy(principles=tuple(il.get("principles", ())),
                                hub_pages=tuple(PageType(p) for p in il.get("hub_pages", ())),
                                evidence_ids=_eids(il["evidence_ids"])),
    )


def _discovery(doc: dict) -> Discovery:
    s, f, so = doc["search"], doc["filtering"], doc["sorting"]
    return Discovery(
        search=SearchStrategy(scope=s.get("scope", "products"), autocomplete=s.get("autocomplete", True),
                              no_results_handling=s.get("no_results_handling", ""),
                              principles=tuple(s.get("principles", ())), evidence_ids=_eids(s["evidence_ids"])),
        filtering=FilteringStrategy(facets=tuple(FilterType(x) for x in f.get("facets", ())),
                                    principles=tuple(f.get("principles", ())), evidence_ids=_eids(f["evidence_ids"])),
        sorting=SortingStrategy(options=tuple(SortOption(x) for x in so.get("options", ())),
                                default=SortOption(so["default"]), evidence_ids=_eids(so["evidence_ids"])),
    )


def _graph(doc: dict) -> IAGraph:
    nodes = tuple(
        IANode(id=IANodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
               evidence_ids=_eids(n["evidence_ids"]))
        for n in doc["nodes"]
    )
    edges = tuple(
        IAEdge(id=IAEdgeId.from_string(e["id"]), source=IANodeId.from_string(e["source"]),
               target=IANodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
        for e in doc["edges"]
    )
    return IAGraph.of(GraphKind(doc["kind"]), nodes, edges)


def _graphs(doc: dict) -> IAGraphs:
    return IAGraphs(
        sitemap=_graph(doc["sitemap"]), navigation=_graph(doc["navigation"]), page=_graph(doc["page"]),
        section=_graph(doc["section"]), relationship=_graph(doc["relationship"]),
        content_tree=_graph(doc["content_tree"]),
    )
