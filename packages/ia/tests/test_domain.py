"""Unit tests for the IA domain — the invariants that make the architecture trustworthy."""

from __future__ import annotations

import pytest

from ia.domain.evidence.evidence import (
    EvidenceGraph,
    IAEvidence,
    InvalidEvidenceError,
)
from ia.domain.graph.ia_graph import IAEdge, IAGraph, IANode, InvalidIAGraphError
from ia.domain.page.goals import PageGoals
from ia.domain.page.page_blueprint import InvalidPageBlueprintError, PageBlueprint
from ia.domain.page.action import PageAction
from ia.domain.section.section import Section
from ia.domain.shared.ids import (
    IAEdgeId,
    IAEvidenceId,
    IANodeId,
    PageActionId,
    PageBlueprintId,
    SectionId,
)
from ia.domain.shared.value_objects import (
    ActionType,
    Confidence,
    GraphKind,
    GraphRelation,
    IAScore,
    NodeKind,
    PageRequirement,
    PageType,
    Percentage,
    Placement,
    Priority,
    ProvenanceKind,
    SectionType,
)
from ia.domain.quality.quality import IAQualityMetrics
from ia.domain.sitemap.sitemap import InvalidSiteMapError, SiteMap


# --- value objects -------------------------------------------------------- #

def test_page_type_and_graph_kind_cardinality() -> None:
    assert len(PageType) == 13
    assert len(GraphKind) == 6


@pytest.mark.parametrize("bad", [-0.01, 1.01])
def test_confidence_rejects_out_of_range(bad: float) -> None:
    with pytest.raises(Exception):
        Confidence(bad)


@pytest.mark.parametrize("bad", [0, 6])
def test_priority_rejects_out_of_range(bad: int) -> None:
    with pytest.raises(Exception):
        Priority(bad)


def test_iascore_bands_are_ordered() -> None:
    assert IAScore.clamp(150.0).value == 100.0
    assert IAScore.clamp(-5.0).value == 0.0


# --- evidence ------------------------------------------------------------- #

def _evidence(ref: str) -> IAEvidence:
    return IAEvidence(
        id=IAEvidenceId.new(), provenance=ProvenanceKind.UX_STRATEGY,
        external_ref=ref, claim=f"claim {ref}", confidence=Confidence(0.8),
    )


def test_evidence_requires_claim_and_ref() -> None:
    with pytest.raises(InvalidEvidenceError):
        IAEvidence(id=IAEvidenceId.new(), provenance=ProvenanceKind.KNOWLEDGE,
                   external_ref="", claim="x", confidence=Confidence(0.5))


def test_evidence_graph_missing_reports_absent_ids() -> None:
    e = _evidence("e1")
    graph = EvidenceGraph.of([e])
    absent = IAEvidenceId.new()
    assert graph.has(e.id)
    assert graph.missing([e.id]) == ()
    assert graph.missing([absent]) == (absent,)


def test_evidence_graph_rejects_duplicate_ids() -> None:
    e = _evidence("e1")
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


# --- ia graph ------------------------------------------------------------- #

def _node() -> IANode:
    return IANode(id=IANodeId.new(), kind=NodeKind.PAGE, label="Home")


def test_ia_graph_rejects_self_loop_edge() -> None:
    n = _node()
    with pytest.raises(InvalidIAGraphError):
        IAEdge(id=IAEdgeId.new(), source=n.id, target=n.id, relation=GraphRelation.CONTAINS)


def test_ia_graph_rejects_dangling_edge() -> None:
    a, b = _node(), _node()
    with pytest.raises(InvalidIAGraphError):
        IAGraph.of(
            GraphKind.SITEMAP, [a],
            [IAEdge(id=IAEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.CONTAINS)],
        )


def test_ia_graph_detects_containment_cycle() -> None:
    a, b = _node(), _node()
    with pytest.raises(InvalidIAGraphError):
        IAGraph.of(
            GraphKind.SITEMAP, [a, b],
            [
                IAEdge(id=IAEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.CONTAINS),
                IAEdge(id=IAEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.CONTAINS),
            ],
        )


def test_ia_graph_allows_mutual_links() -> None:
    a, b = _node(), _node()
    graph = IAGraph.of(
        GraphKind.NAVIGATION, [a, b],
        [
            IAEdge(id=IAEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.LINKS_TO),
            IAEdge(id=IAEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.LINKS_TO),
        ],
    )
    assert len(graph) == 2
    assert graph.successors(a.id)[0].id == b.id


# --- site map / page blueprint -------------------------------------------- #

def _page(page_type: PageType, requirement: PageRequirement, *, with_section: bool = True) -> PageBlueprint:
    section = (
        Section(id=SectionId.new(), type=SectionType.HERO, purpose="orient", is_required=True),
    ) if with_section else ()
    return PageBlueprint(
        id=PageBlueprintId.new(), page_type=page_type, requirement=requirement,
        purpose=f"{page_type.value} purpose",
        goals=PageGoals(business_goal="sell", primary_user_goal="buy"),
        required_sections=section,
    )


def test_sitemap_rejects_duplicate_page_type() -> None:
    with pytest.raises(InvalidSiteMapError):
        SiteMap.of([
            _page(PageType.PRODUCT, PageRequirement.REQUIRED),
            _page(PageType.PRODUCT, PageRequirement.REQUIRED),
        ])


def test_sitemap_allows_duplicate_custom_cms() -> None:
    site = SiteMap.of([
        _page(PageType.CUSTOM_CMS, PageRequirement.OPTIONAL),
        _page(PageType.CUSTOM_CMS, PageRequirement.OPTIONAL),
    ])
    assert len(site) == 2


def test_sitemap_partitions_required_and_optional() -> None:
    site = SiteMap.of([
        _page(PageType.HOMEPAGE, PageRequirement.REQUIRED),
        _page(PageType.WISHLIST, PageRequirement.OPTIONAL),
    ])
    assert {p.page_type for p in site.required()} == {PageType.HOMEPAGE}
    assert {p.page_type for p in site.optional()} == {PageType.WISHLIST}


def test_page_blueprint_rejects_non_primary_in_primary_actions() -> None:
    with pytest.raises(InvalidPageBlueprintError):
        PageBlueprint(
            id=PageBlueprintId.new(), page_type=PageType.PRODUCT,
            requirement=PageRequirement.REQUIRED, purpose="buy",
            goals=PageGoals(business_goal="sell", primary_user_goal="buy"),
            primary_actions=(
                PageAction(id=PageActionId.new(), type=ActionType.SECONDARY,
                           action="wishlist", placement=Placement.ABOVE_FOLD),
            ),
        )


# --- quality -------------------------------------------------------------- #

def test_quality_overall_score_weighting_and_band() -> None:
    perfect = IAQualityMetrics(
        coverage=Percentage(1.0), grounding=Percentage(1.0),
        completeness=Percentage(1.0), confidence=Confidence(1.0),
    )
    assert perfect.overall_score.value == 100.0
    assert perfect.is_fully_grounded

    partial = IAQualityMetrics(
        coverage=Percentage(0.5), grounding=Percentage(0.8),
        completeness=Percentage(0.4), confidence=Confidence(0.6),
    )
    # 0.3*0.5 + 0.3*0.8 + 0.25*0.4 + 0.15*0.6 = 0.15+0.24+0.10+0.09 = 0.58 → 58
    assert partial.overall_score.value == pytest.approx(58.0)
    assert not partial.is_fully_grounded
