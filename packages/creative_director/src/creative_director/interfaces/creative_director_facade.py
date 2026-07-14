"""The Creative Director facade — the inbound entry point of the engine.

The single surface everything above the engine calls: an API, the orchestration layer, or
tests. It runs the review, retrieves reviews, projects them into views and the neutral
approval bundle, applies human overrides and committee rulings (each a new version), and
explains a graph node — returning serializable views, never domain aggregates.

``can_proceed`` is the platform's go/no-go gate: the orchestration layer advances a run only
when the Creative Director says it may.
"""

from __future__ import annotations

from core.errors import NotFoundError

from creative_director.application.commands import (
    BuildReview,
    CommitteeVote,
    OverrideDecision,
)
from creative_director.application.creative_director_engine import CreativeDirectorEngine
from creative_director.application.ports.clock import Clock
from creative_director.application.ports.unit_of_work import UnitOfWorkFactory
from creative_director.domain.decision.approval import ApprovalDecision
from creative_director.domain.decision.history import DecisionRecord
from creative_director.domain.report.bundle import ApprovalBundle
from creative_director.domain.report.report import CreativeDirectorReview
from creative_director.domain.shared.ids import (
    CDNodeId,
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
    DecisionId,
)
from creative_director.domain.shared.value_objects import (
    ApprovalStatus,
    DeciderRole,
    GraphKind,
    ReviewDimension,
)
from creative_director.interfaces.dto import (
    ApprovalBundleView,
    ApprovalView,
    DimensionView,
    GraphView,
    ReviewView,
    ScorecardView,
    TraceView,
)

__all__ = ["CreativeDirectorFacade"]


class CreativeDirectorFacade:
    """Review, retrieve, rule, and explain — commands in, views out."""

    def __init__(
        self,
        engine: CreativeDirectorEngine,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory
        self._clock = clock

    # -- build & retrieve -------------------------------------------------- #
    async def review(self, command: BuildReview) -> ReviewView:
        """Run the full pipeline and return the produced review view."""
        review = await self._engine.build(command)
        return ReviewView.from_review(review)

    async def get(self, review_id: CreativeDirectorReviewId) -> ReviewView:
        return ReviewView.from_review(await self._load(review_id))

    async def latest(self, lineage_id: CreativeDirectorReviewLineageId) -> ReviewView:
        async with self._uow() as uow:
            review = await uow.reviews.latest(lineage_id)
        return ReviewView.from_review(review)

    async def history(
        self, lineage_id: CreativeDirectorReviewLineageId
    ) -> list[ReviewView]:
        async with self._uow() as uow:
            reviews = await uow.reviews.history(lineage_id)
        return [ReviewView.from_review(r) for r in reviews]

    # -- projections ------------------------------------------------------- #
    async def dimension(
        self, review_id: CreativeDirectorReviewId, dimension: ReviewDimension
    ) -> DimensionView:
        view = await self.get(review_id)
        for dr in view.dimension_reviews:
            if dr["dimension"] == dimension.value:
                return DimensionView(dimension=dr)
        raise NotFoundError(
            f"Dimension {dimension.value} not found in review {review_id}.",
            details={"dimension": dimension.value},
        )

    async def scorecard(self, review_id: CreativeDirectorReviewId) -> ScorecardView:
        return ScorecardView(scorecard=(await self.get(review_id)).scorecard)

    async def approval(self, review_id: CreativeDirectorReviewId) -> ApprovalView:
        return ApprovalView(approval=(await self.get(review_id)).approval)

    async def can_proceed(self, review_id: CreativeDirectorReviewId) -> bool:
        return (await self._load(review_id)).can_proceed

    async def required_changes(self, review_id: CreativeDirectorReviewId) -> list[dict]:
        return (await self.get(review_id)).improvement_matrix

    async def decision_history(self, review_id: CreativeDirectorReviewId) -> list[dict]:
        return (await self.get(review_id)).decision_history

    async def quality_matrix(self, review_id: CreativeDirectorReviewId) -> list[dict]:
        return (await self.get(review_id)).quality_matrix

    async def improvement_matrix(self, review_id: CreativeDirectorReviewId) -> list[dict]:
        return (await self.get(review_id)).improvement_matrix

    async def graph(
        self, review_id: CreativeDirectorReviewId, kind: GraphKind
    ) -> GraphView:
        return GraphView(graph=(await self.get(review_id)).graphs[kind.value])

    async def approval_bundle(
        self, review_id: CreativeDirectorReviewId
    ) -> ApprovalBundleView:
        """Project a review into the neutral ruling a downstream phase acts on."""
        review = await self._load(review_id)
        return ApprovalBundleView.from_bundle(ApprovalBundle.from_review(review))

    # -- human rulings ----------------------------------------------------- #
    async def override(self, command: OverrideDecision) -> ReviewView:
        """Apply a human Creative Director's ruling, superseding the automatic one."""
        review = await self._load(command.review_id)
        decision = ApprovalDecision(
            id=DecisionId.new(), status=command.status, rationale=command.rationale,
            decided_by=DeciderRole.CREATIVE_DIRECTOR, decided_at=self._clock.now(),
            overall_score=review.scorecard.overall,
            failing_gates=() if command.status is ApprovalStatus.APPROVED else review.failing_gates(),
            blocking_finding_ids=(),
            evidence_ids=review.approval.evidence_ids,
        )
        return await self._supersede(review, decision)

    async def committee(self, command: CommitteeVote) -> ReviewView:
        """Aggregate committee ballots into a ruling, superseding the automatic one."""
        review = await self._load(command.review_id)
        status = self._aggregate(command)
        rationale = (
            f"Committee ruling ({len(command.ballots)} ballots, "
            f"{'unanimous' if command.require_unanimous else 'majority'}): {status.value}."
        )
        decision = ApprovalDecision(
            id=DecisionId.new(), status=status, rationale=rationale,
            decided_by=DeciderRole.COMMITTEE, decided_at=self._clock.now(),
            overall_score=review.scorecard.overall,
            failing_gates=() if status is ApprovalStatus.APPROVED else review.failing_gates(),
            blocking_finding_ids=(),
            evidence_ids=review.approval.evidence_ids,
        )
        return await self._supersede(review, decision)

    # -- explain ----------------------------------------------------------- #
    async def explain(
        self, review_id: CreativeDirectorReviewId, graph_kind: GraphKind, node_id: CDNodeId
    ) -> TraceView:
        """Explain one graph node by resolving its successors and cited evidence."""
        review = await self._load(review_id)
        graph = review.graphs.get(graph_kind)
        if not graph.has(node_id):
            raise NotFoundError(
                f"Node {node_id} not found in the {graph_kind.value} graph of {review_id}.",
                details={"node_id": str(node_id)},
            )
        node = graph.get(node_id)
        successors = graph.successors(node_id)
        evidence = [
            {
                "id": str(e.id), "provenance": e.provenance.value,
                "external_ref": e.external_ref, "claim": e.claim,
                "confidence": e.confidence.value, "source_name": e.source_name,
            }
            for eid in node.evidence_ids
            if review.evidence_graph.has(eid)
            for e in (review.evidence_graph.get(eid),)
        ]
        return TraceView(
            node={"id": str(node.id), "kind": node.kind.value, "label": node.label},
            successors=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label} for n in successors
            ],
            evidence=evidence,
        )

    # ------------------------------------------------------------------ #
    async def _load(
        self, review_id: CreativeDirectorReviewId
    ) -> CreativeDirectorReview:
        async with self._uow() as uow:
            return await uow.reviews.get(review_id)

    async def _supersede(
        self, review: CreativeDirectorReview, decision: ApprovalDecision
    ) -> ReviewView:
        now = decision.decided_at
        async with self._uow() as uow:
            history = await uow.reviews.history(review.lineage_id)
        version = len(history) + 1
        record = DecisionRecord(
            decision_id=decision.id, status=decision.status, decided_by=decision.decided_by,
            decided_at=now, rationale=decision.rationale, version=version,
        )
        superseded = CreativeDirectorReview(
            id=CreativeDirectorReviewId.new(),
            lineage_id=review.lineage_id, version=version, project_id=review.project_id,
            subject=review.subject, policy=review.policy,
            dimension_reviews=review.dimension_reviews, scorecard=review.scorecard,
            approval=decision,
            decision_history=review.decision_history.append(record),
            quality_matrix=review.quality_matrix,
            improvement_matrix=review.improvement_matrix, graphs=review.graphs,
            evidence_graph=review.evidence_graph, quality=review.quality, created_at=now,
        )
        async with self._uow() as uow:
            await uow.reviews.save(superseded)
            await uow.commit()
        return ReviewView.from_review(superseded)

    @staticmethod
    def _aggregate(command: CommitteeVote) -> ApprovalStatus:
        approvals = sum(1 for b in command.ballots if b.status is ApprovalStatus.APPROVED)
        total = len(command.ballots)
        if total == 0:
            return ApprovalStatus.ESCALATED
        if command.require_unanimous:
            return ApprovalStatus.APPROVED if approvals == total else ApprovalStatus.CHANGES_REQUESTED
        return ApprovalStatus.APPROVED if approvals * 2 > total else ApprovalStatus.CHANGES_REQUESTED
