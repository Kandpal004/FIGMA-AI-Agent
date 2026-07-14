"""Behavioural tests for the Creative Director engine — end-to-end through the facade."""

from __future__ import annotations

import pytest

from creative_director.application.commands import (
    BuildReview,
    CommitteeBallot,
    CommitteeVote,
    OverrideDecision,
)
from creative_director.domain.shared.ids import CreativeDirectorReviewId, CreativeDirectorReviewLineageId
from creative_director.domain.shared.value_objects import (
    ApprovalStatus,
    GraphKind,
    ReviewDimension,
    ReviewMode,
    ReviewProfileKind,
)

pytestmark = pytest.mark.asyncio


async def test_strong_subject_is_approved_and_can_proceed(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    v = await env.facade.review(BuildReview(request=request_factory()))
    assert v.approval["status"] == ApprovalStatus.APPROVED.value
    assert v.can_proceed
    assert v.quality.grounding == 1.0
    assert v.dimension_count == 16
    assert len(v.scorecard) == 15  # 14 substantive + overall
    assert v.evidence_count > 0


async def test_all_five_graphs_are_populated(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    v = await env.facade.review(BuildReview(request=request_factory()))
    assert set(v.graphs.keys()) == {g.value for g in GraphKind}
    for kind, g in v.graphs.items():
        assert g["nodes"], f"graph {kind} has no nodes"


async def test_weak_subject_is_rejected_with_anti_patterns(env_factory, request_factory, weak_signals) -> None:
    """The Creative Director rejects a generic, purpose-free (AI/Dribbble) design."""
    env = env_factory(weak_signals)
    v = await env.facade.review(BuildReview(request=request_factory()))
    assert v.approval["status"] == ApprovalStatus.REJECTED.value
    assert not v.can_proceed
    antis = {a for dr in v.dimension_reviews for a in dr["anti_patterns"]}
    assert {"generic_ai_pattern", "low_trust", "poor_cro", "weak_hierarchy"} & antis
    blocking = {dr["dimension"] for dr in v.dimension_reviews if dr["blocking_issues"]}
    assert {"trust_signals", "conversion_strategy", "business_alignment"} <= blocking


async def test_profile_reweights_the_overall(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    startup = await env.facade.review(BuildReview(request=request_factory(profile=ReviewProfileKind.STARTUP)))
    luxury = await env.facade.review(BuildReview(request=request_factory(profile=ReviewProfileKind.LUXURY)))
    # Same evidence, different profile weighting → the overall scores differ.
    assert startup.scorecard["overall"]["score"] != luxury.scorecard["overall"]["score"] or (
        startup.scorecard["business"]["weight"] != luxury.scorecard["business"]["weight"]
    )
    # Luxury weights brand more heavily than startup.
    assert luxury.scorecard["brand"]["weight"] > startup.scorecard["brand"]["weight"]


async def test_configurable_threshold_flips_the_verdict(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    # An impossibly high threshold turns an otherwise-approved review into changes requested.
    from creative_director.domain.shared.value_objects import Score
    v = await env.facade.review(BuildReview(request=request_factory(threshold=Score(99.9))))
    assert v.approval["status"] == ApprovalStatus.CHANGES_REQUESTED.value


async def test_every_dimension_reviewed_and_scored(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    v = await env.facade.review(BuildReview(request=request_factory()))
    reviewed = {dr["dimension"] for dr in v.dimension_reviews}
    assert reviewed == {d.value for d in ReviewDimension}
    for dr in v.dimension_reviews:
        assert 0.0 <= dr["quality_score"] <= 100.0
        assert dr["notes"]


async def test_human_assisted_escalates_then_override_approves(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    v = await env.facade.review(BuildReview(request=request_factory(mode=ReviewMode.HUMAN_ASSISTED)))
    assert v.approval["status"] == ApprovalStatus.ESCALATED.value
    assert not v.can_proceed  # escalated is not approved
    ov = await env.facade.override(OverrideDecision(
        review_id=CreativeDirectorReviewId.from_string(v.review_id),
        status=ApprovalStatus.APPROVED, rationale="Human CD confirms the recommendation.",
    ))
    assert ov.version == 2
    assert ov.approval["status"] == ApprovalStatus.APPROVED.value
    assert ov.approval["decided_by"] == "creative_director"
    assert ov.can_proceed
    assert len(ov.decision_history) == 2


async def test_creative_director_can_veto_an_approved_design(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    v = await env.facade.review(BuildReview(request=request_factory()))
    assert v.approval["status"] == ApprovalStatus.APPROVED.value
    ov = await env.facade.override(OverrideDecision(
        review_id=CreativeDirectorReviewId.from_string(v.review_id),
        status=ApprovalStatus.REJECTED, rationale="Reads generic; needs a stronger point of view.",
    ))
    assert ov.approval["status"] == ApprovalStatus.REJECTED.value
    assert not ov.can_proceed


async def test_committee_majority_rules(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    v = await env.facade.review(BuildReview(request=request_factory(mode=ReviewMode.REVIEW_COMMITTEE)))
    assert v.approval["status"] == ApprovalStatus.ESCALATED.value
    ov = await env.facade.committee(CommitteeVote(
        review_id=CreativeDirectorReviewId.from_string(v.review_id),
        ballots=(
            CommitteeBallot(reviewer="a", status=ApprovalStatus.APPROVED),
            CommitteeBallot(reviewer="b", status=ApprovalStatus.APPROVED),
            CommitteeBallot(reviewer="c", status=ApprovalStatus.CHANGES_REQUESTED),
        ),
    ))
    assert ov.approval["status"] == ApprovalStatus.APPROVED.value
    assert ov.approval["decided_by"] == "committee"


async def test_improvement_matrix_ranks_blocking_first(env_factory, request_factory, weak_signals) -> None:
    env = env_factory(weak_signals)
    v = await env.facade.review(BuildReview(request=request_factory()))
    matrix = v.improvement_matrix
    assert matrix
    # Blocking changes come before non-blocking ones.
    blocking_flags = [c["blocking"] for c in matrix]
    assert blocking_flags == sorted(blocking_flags, reverse=True)


async def test_determinism_same_input_same_verdict(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    a = await env.facade.review(BuildReview(request=request_factory()))
    b = await env.facade.review(BuildReview(request=request_factory()))
    assert a.scorecard["overall"]["score"] == b.scorecard["overall"]["score"]
    assert a.approval["status"] == b.approval["status"]


async def test_rebuild_under_lineage_bumps_version(env_factory, request_factory, strong_signals) -> None:
    env = env_factory(strong_signals)
    v1 = await env.facade.review(BuildReview(request=request_factory()))
    lineage = CreativeDirectorReviewLineageId.from_string(v1.lineage_id)
    v2 = await env.facade.review(BuildReview(request=request_factory(), lineage_id=lineage))
    assert v2.version == 2
    history = await env.facade.history(lineage)
    assert [h.version for h in history] == [1, 2]
