"""Domain-layer tests: value objects, taxonomy, status machine, applicability,
query matching, and entry versioning."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from knowledge.domain.entry.applicability import Applicability
from knowledge.domain.entry.entry import InvalidKnowledgeEntryError, KnowledgeEntry
from knowledge.domain.entry.source import Source, SourceKind
from knowledge.domain.entry.status import (
    IllegalStatusTransitionError,
    KnowledgeStatus,
    KnowledgeStatusMachine,
)
from knowledge.domain.reasoning.query import KnowledgeQuery
from knowledge.domain.shared.value_objects import (
    Confidence,
    ConfidenceLevel,
    InvalidKnowledgeValueError,
    KnowledgeScope,
    Platform,
    Priority,
    Tag,
)
from knowledge.domain.taxonomy.category import KnowledgeCategory

_NOW = datetime(2026, 7, 13, tzinfo=UTC)
_SRC = Source(name="NNG", kind=SourceKind.RESEARCH_INSTITUTE)


def _entry(**kw) -> KnowledgeEntry:
    defaults = dict(
        category=KnowledgeCategory.UX_LAWS, title="T", statement="S",
        description="D", source=_SRC, at=_NOW,
    )
    defaults.update(kw)
    return KnowledgeEntry.create(**defaults)


# --------------------------- value objects ------------------------------ #
def test_confidence_levels_and_ordering() -> None:
    assert Confidence.of(0.95).level is ConfidenceLevel.ESTABLISHED
    assert Confidence.of(0.6).level is ConfidenceLevel.MODERATE
    assert Confidence.of(0.9) > Confidence.of(0.5)
    with pytest.raises(InvalidKnowledgeValueError):
        Confidence.of(1.5)


def test_priority_ordering() -> None:
    assert Priority.CRITICAL > Priority.HIGH > Priority.NORMAL > Priority.LOW


def test_tag_normalization() -> None:
    assert Tag.of("Above The Fold").value == "above-the-fold"
    assert Tag.of("  CRO ") == Tag.of("cro")


def test_scope_visibility() -> None:
    t = uuid.uuid4()
    assert KnowledgeScope.global_().visible_to(None)
    assert KnowledgeScope.tenant(t).visible_to(t)
    assert not KnowledgeScope.tenant(t).visible_to(uuid.uuid4())


def test_seventeen_categories() -> None:
    assert len(list(KnowledgeCategory)) == 17


# --------------------------- status machine ----------------------------- #
def test_status_machine_integrity() -> None:
    KnowledgeStatusMachine.verify_integrity()


@pytest.mark.parametrize(
    "src,tgt,legal",
    [
        (KnowledgeStatus.DRAFT, KnowledgeStatus.PROPOSED, True),
        (KnowledgeStatus.PROPOSED, KnowledgeStatus.ACTIVE, True),
        (KnowledgeStatus.ACTIVE, KnowledgeStatus.SUPERSEDED, True),
        (KnowledgeStatus.DEPRECATED, KnowledgeStatus.ACTIVE, True),
        (KnowledgeStatus.DRAFT, KnowledgeStatus.ACTIVE, False),
        (KnowledgeStatus.ARCHIVED, KnowledgeStatus.ACTIVE, False),
    ],
)
def test_status_transitions(src, tgt, legal) -> None:
    machine = KnowledgeStatusMachine()
    assert machine.is_legal(src, tgt) is legal
    if not legal:
        with pytest.raises(IllegalStatusTransitionError):
            machine.validate(src, tgt)


# --------------------------- applicability ------------------------------ #
def test_applicability_matching_and_specificity() -> None:
    app = Applicability.build(
        page_types=["product"], platforms=[Platform.SHOPIFY_PLUS],
        contexts=[Tag.of("above the fold")],
    )
    assert app.matches(page_type="product", platform=Platform.SHOPIFY_PLUS)
    assert app.matches(page_type=None)  # unspecified never filters
    assert not app.matches(page_type="cart")
    assert not app.matches(platform=Platform.MAGENTO)
    assert app.specificity() == 3
    assert Applicability.any().is_universal
    assert Applicability.build(platforms=[Platform.AGNOSTIC]).matches(platform=Platform.MAGENTO)


# --------------------------- entry + query ------------------------------ #
def test_entry_versioning_preserves_lineage() -> None:
    v1 = _entry(confidence=Confidence.of(0.9)).with_status(KnowledgeStatus.ACTIVE, at=_NOW)
    v2 = v1.revise(at=_NOW, statement="revised", priority=Priority.CRITICAL)
    assert v2.version == 2 and v2.knowledge_id == v1.knowledge_id and v2.id != v1.id
    assert v2.status is KnowledgeStatus.DRAFT and v2.priority is Priority.CRITICAL
    assert v1.statement == "S"  # original immutable


def test_entry_validation() -> None:
    with pytest.raises(InvalidKnowledgeEntryError):
        _entry(title=" ")


def test_query_matching_defaults_to_active_and_scope() -> None:
    draft = _entry()
    active = _entry().with_status(KnowledgeStatus.ACTIVE, at=_NOW)
    assert KnowledgeQuery().matches(active)
    assert not KnowledgeQuery().matches(draft)  # default statuses = {ACTIVE}

    t = uuid.uuid4()
    tenant_entry = _entry(scope=KnowledgeScope.tenant(t)).with_status(
        KnowledgeStatus.ACTIVE, at=_NOW
    )
    assert not KnowledgeQuery().matches(tenant_entry)  # global viewer
    assert KnowledgeQuery(viewer_tenant_id=t).matches(tenant_entry)
