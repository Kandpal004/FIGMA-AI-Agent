"""Unit tests for the design-language domain — the invariants that make a language trustworthy."""

from __future__ import annotations

import pytest

from design_language.domain.dna.visual_dna import InvalidVisualDNAError, VisualDNA
from design_language.domain.evidence.evidence import (
    DLEvidence,
    EvidenceGraph,
    InvalidEvidenceError,
)
from design_language.domain.graph.dl_graph import DLEdge, DLGraph, DLNode, InvalidDLGraphError
from design_language.domain.language.selection import InvalidSelectionError, LanguageSelection
from design_language.domain.philosophy.philosophy import InvalidPhilosophyError, Philosophy, PhilosophySet
from design_language.domain.quality.quality import DesignLanguageQualityMetrics
from design_language.domain.shared.ids import (
    DLEdgeId,
    DLEvidenceId,
    DLNodeId,
    PhilosophyId,
)
from design_language.domain.shared.value_objects import (
    ColorStrategy,
    Confidence,
    ConsideredAlternative,
    ContrastLevel,
    Density,
    GraphKind,
    GraphRelation,
    IndustryPreset,
    LanguageArchetype,
    Level,
    NodeKind,
    Percentage,
    PhilosophyKind,
    ProvenanceKind,
    Ratio,
    Rhythm,
    Tag,
    VisualStyle,
    VisualWeight,
)
from design_language.domain.tokens.color import ColorPhilosophy


def test_cardinalities() -> None:
    assert len(LanguageArchetype) == 19  # 18 named + custom blend
    assert len(IndustryPreset) == 12
    assert len(GraphKind) == 2


@pytest.mark.parametrize("bad", [0, 6])
def test_level_range(bad: int) -> None:
    with pytest.raises(Exception):
        Level(bad)


def test_ratio_must_exceed_one() -> None:
    with pytest.raises(Exception):
        Ratio(1.0)


# --- evidence ------------------------------------------------------------- #

def _ev(ref: str) -> DLEvidence:
    return DLEvidence(id=DLEvidenceId.new(), provenance=ProvenanceKind.BRAND_STRATEGY,
                      external_ref=ref, claim=f"c {ref}", confidence=Confidence(0.8))


def test_evidence_graph_missing_and_duplicate() -> None:
    e = _ev("e1")
    g = EvidenceGraph.of([e])
    absent = DLEvidenceId.new()
    assert g.missing([e.id]) == () and g.missing([absent]) == (absent,)
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


# --- DNA ------------------------------------------------------------------ #

def _dna(traits=("refined", "calm")) -> VisualDNA:
    return VisualDNA(
        visual_style=VisualStyle.MINIMAL, luxury_level=Level(5), minimalism_level=Level(5),
        density=Density.SPACIOUS, visual_weight=VisualWeight.LIGHT, contrast=ContrastLevel.HIGH,
        rhythm=Rhythm.RELAXED, essence="restrained and precise",
        traits=tuple(Tag.of(t) for t in traits),
    )


def test_dna_requires_essence() -> None:
    with pytest.raises(InvalidVisualDNAError):
        VisualDNA(visual_style=VisualStyle.MINIMAL, luxury_level=Level(3), minimalism_level=Level(3),
                  density=Density.COMFORTABLE, visual_weight=VisualWeight.BALANCED,
                  contrast=ContrastLevel.MEDIUM, rhythm=Rhythm.MEASURED, essence="  ")


def test_dna_distinctiveness() -> None:
    assert _dna(("a", "b")).is_distinctive
    assert not _dna(("only",)).is_distinctive


# --- graph ---------------------------------------------------------------- #

def _node() -> DLNode:
    return DLNode(id=DLNodeId.new(), kind=NodeKind.PHILOSOPHY, label="p")


def test_graph_is_acyclic() -> None:
    a, b = _node(), _node()
    with pytest.raises(InvalidDLGraphError):
        DLGraph.of(GraphKind.VISUAL, [a, b], [
            DLEdge(id=DLEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.ELABORATES),
            DLEdge(id=DLEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.ELABORATES),
        ])


def test_graph_rejects_dangling_edge() -> None:
    a, b = _node(), _node()
    with pytest.raises(InvalidDLGraphError):
        DLGraph.of(GraphKind.LANGUAGE, [a], [
            DLEdge(id=DLEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.REJECTS),
        ])


# --- language selection --------------------------------------------------- #

def test_selection_requires_a_considered_alternative() -> None:
    with pytest.raises(InvalidSelectionError):
        LanguageSelection(
            archetype=LanguageArchetype.AESOP, rationale="fits the brand",
            business_alignment="advances conversion", considered=(),
        )


def test_selection_with_alternative_is_valid() -> None:
    sel = LanguageSelection(
        archetype=LanguageArchetype.AESOP, rationale="fits the brand",
        business_alignment="advances conversion",
        considered=(ConsideredAlternative(option="luxury_beauty", reason_rejected="too overtly luxe"),),
    )
    assert len(sel.considered) == 1


# --- philosophy & color --------------------------------------------------- #

def test_philosophy_set_rejects_duplicate_kind() -> None:
    p1 = Philosophy(id=PhilosophyId.new(), kind=PhilosophyKind.SPACING, approach="a")
    p2 = Philosophy(id=PhilosophyId.new(), kind=PhilosophyKind.SPACING, approach="b")
    with pytest.raises(InvalidPhilosophyError):
        PhilosophySet.of([p1, p2])


def test_color_accent_count_non_negative() -> None:
    with pytest.raises(Exception):
        ColorPhilosophy(strategy=ColorStrategy.MONOCHROME, accent_count=-1)


# --- quality -------------------------------------------------------------- #

def test_quality_weighting() -> None:
    q = DesignLanguageQualityMetrics(
        coverage=Percentage(1.0), grounding=Percentage(1.0),
        consistency=Percentage(1.0), confidence=Confidence(1.0),
    )
    assert q.overall_score.value == 100.0 and q.is_fully_grounded
    partial = DesignLanguageQualityMetrics(
        coverage=Percentage(0.5), grounding=Percentage(0.8),
        consistency=Percentage(0.4), confidence=Confidence(0.6),
    )
    # 0.3*0.5 + 0.3*0.8 + 0.25*0.4 + 0.15*0.6 = 0.58 → 58
    assert partial.overall_score.value == pytest.approx(58.0)
