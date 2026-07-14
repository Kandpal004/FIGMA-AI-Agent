"""The CreativeDirectorEngine — the orchestrator of the review-and-approval pipeline.

Given a command, it runs the full pipeline in fixed order — assemble inputs → consolidate
evidence → review through the critic panel → validate grounding → score → evaluate approval →
build matrices and graphs → assemble — producing a single, provenance-tracked, immutable,
versioned :class:`CreativeDirectorReview`.

It is a *deterministic* review system, not an LLM wrapper: the panel and input ports are the
only swappable seams, and the scoring, gate, threshold, and approval logic are pure domain
code the model cannot bypass. Because the review validates provenance and decision integrity
at construction, an ungrounded ruling or an approval inconsistent with its own scores cannot
be produced. Every collaborator is injected, so the engine is framework-independent and
testable with fakes.

The panel *proposes* the findings and the deterministic stages *dispose* — the port proposes,
the domain disposes, and the Creative Director's authority is the domain's.
"""

from __future__ import annotations

from datetime import datetime

from creative_director.application.commands import BuildReview
from creative_director.application.pipeline.approval_evaluator import ApprovalEvaluator
from creative_director.application.pipeline.evidence_consolidator import EvidenceConsolidator
from creative_director.application.pipeline.finding_validator import FindingValidator
from creative_director.application.pipeline.graph_builder import GraphBuilder
from creative_director.application.pipeline.input_assembler import InputAssembler
from creative_director.application.pipeline.matrix_builder import MatrixBuilder
from creative_director.application.pipeline.scorer import Scorer
from creative_director.application.ports.brand_input import BrandInputPort
from creative_director.application.ports.business_strategy_input import BusinessStrategyInputPort
from creative_director.application.ports.clock import Clock
from creative_director.application.ports.competitor_insight import CompetitorInsightPort
from creative_director.application.ports.ia_input import IAInputPort
from creative_director.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from creative_director.application.ports.psychology_input import PsychologyInputPort
from creative_director.application.ports.reasoning import ReasoningPort
from creative_director.application.ports.research_input import ResearchInputPort
from creative_director.application.ports.review_panel import ReviewPanelPort
from creative_director.application.ports.unit_of_work import UnitOfWorkFactory
from creative_director.application.ports.ux_input import UXInputPort
from creative_director.application.ports.wireframe_input import WireframeInputPort
from creative_director.domain.decision.approval import ApprovalDecision
from creative_director.domain.decision.history import DecisionHistory, DecisionRecord
from creative_director.domain.graph.graphs import CreativeDirectorGraphs
from creative_director.domain.quality.quality import ReviewQualityMetrics
from creative_director.domain.report.report import CreativeDirectorReview
from creative_director.domain.scoring.scorecard import Scorecard
from creative_director.domain.shared.ids import (
    CreativeDirectorReviewId,
    CreativeDirectorReviewLineageId,
)
from creative_director.domain.shared.value_objects import (
    Confidence,
    Percentage,
    ReviewDimension,
)

__all__ = ["CreativeDirectorEngine"]


class CreativeDirectorEngine:
    """Runs the review pipeline and persists a Creative Director review."""

    def __init__(
        self,
        *,
        wireframe: WireframeInputPort,
        ia: IAInputPort,
        ux: UXInputPort,
        business_strategy: BusinessStrategyInputPort,
        brand: BrandInputPort,
        psychology: PsychologyInputPort,
        knowledge: KnowledgeAdvisorPort,
        research: ResearchInputPort,
        competitor: CompetitorInsightPort,
        reasoning: ReasoningPort,
        panel: ReviewPanelPort,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        input_assembler: InputAssembler | None = None,
        consolidator: EvidenceConsolidator | None = None,
        finding_validator: FindingValidator | None = None,
        scorer: Scorer | None = None,
        approval_evaluator: ApprovalEvaluator | None = None,
        graph_builder: GraphBuilder | None = None,
        matrix_builder: MatrixBuilder | None = None,
    ) -> None:
        self._wireframe = wireframe
        self._ia = ia
        self._ux = ux
        self._business_strategy = business_strategy
        self._brand = brand
        self._psychology = psychology
        self._knowledge = knowledge
        self._research = research
        self._competitor = competitor
        self._reasoning = reasoning
        self._panel = panel
        self._uow = unit_of_work_factory
        self._clock = clock
        self._input = input_assembler or InputAssembler()
        self._consolidator = consolidator or EvidenceConsolidator()
        self._validator = finding_validator or FindingValidator()
        self._scorer = scorer or Scorer()
        self._approval = approval_evaluator or ApprovalEvaluator()
        self._graphs = graph_builder or GraphBuilder()
        self._matrices = matrix_builder or MatrixBuilder()

    async def build(self, command: BuildReview) -> CreativeDirectorReview:
        """Run the full pipeline and persist the resulting review."""
        now = self._clock.now()
        request = command.request

        # 1. Assemble inputs from every signal port.
        review_input = await self._input.assemble(
            request,
            wireframe=self._wireframe, ia=self._ia, ux=self._ux,
            business_strategy=self._business_strategy, brand=self._brand,
            psychology=self._psychology, knowledge=self._knowledge, research=self._research,
            competitor=self._competitor, reasoning=self._reasoning,
        )

        # 2. Consolidate every signal into one cited evidence graph.
        evidence = self._consolidator.consolidate(review_input.signals)

        # 3–4. Review across the sixteen dimensions, then validate grounding.
        draft = await self._panel.review(review_input, evidence)
        self._validator.validate(draft, evidence)
        dimension_reviews = draft.dimension_reviews

        # 5. Score, 6. evaluate approval.
        scorecard = self._scorer.score(dimension_reviews, request.policy.profile)
        approval = self._approval.evaluate(scorecard, dimension_reviews, request.policy, now)

        # 7. Build matrices and graphs.
        changes = self._matrices.collect_changes(dimension_reviews)
        quality_matrix = self._matrices.quality(scorecard)
        improvement_matrix = self._matrices.improvement(dimension_reviews)
        graphs = self._graphs.build(
            request.subject.label or request.subject.reference,
            dimension_reviews, scorecard, approval, changes,
        )

        # 8. Assemble the versioned review (invariants fire here).
        version = await self._next_version(command.lineage_id)
        history = await self._decision_history(command.lineage_id, approval, now, version)
        review = CreativeDirectorReview(
            id=CreativeDirectorReviewId.new(),
            lineage_id=command.lineage_id or CreativeDirectorReviewLineageId.new(),
            version=version,
            project_id=request.project_id,
            subject=request.subject,
            policy=request.policy,
            dimension_reviews=dimension_reviews,
            scorecard=scorecard,
            approval=approval,
            decision_history=history,
            quality_matrix=quality_matrix,
            improvement_matrix=improvement_matrix,
            graphs=graphs,
            evidence_graph=evidence,
            quality=self._quality(dimension_reviews, graphs, scorecard),
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.reviews.save(review)
            await uow.commit()
        return review

    # ------------------------------------------------------------------ #
    async def _next_version(
        self, lineage_id: CreativeDirectorReviewLineageId | None
    ) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.reviews.history(lineage_id)
        return len(history) + 1

    async def _decision_history(
        self,
        lineage_id: CreativeDirectorReviewLineageId | None,
        approval: ApprovalDecision,
        now: datetime,
        version: int,
    ) -> DecisionHistory:
        prior = DecisionHistory()
        if lineage_id is not None:
            async with self._uow() as uow:
                history = await uow.reviews.history(lineage_id)
            if history:
                prior = history[-1].decision_history
        record = DecisionRecord(
            decision_id=approval.id, status=approval.status, decided_by=approval.decided_by,
            decided_at=now, rationale=approval.rationale, version=version,
        )
        return prior.append(record)

    @staticmethod
    def _quality(
        dimension_reviews, graphs: CreativeDirectorGraphs, scorecard: Scorecard
    ) -> ReviewQualityMetrics:
        covered = len({dr.dimension for dr in dimension_reviews})
        coverage = Percentage.ratio(covered, len(ReviewDimension))

        citable: list[tuple] = []
        for dr in dimension_reviews:
            citable.append(dr.evidence_ids)
            for finding in dr.findings:
                citable.append(finding.evidence_ids)
            for change in dr.required_changes:
                citable.append(change.evidence_ids)
        for cs in scorecard.scores:
            citable.append(cs.evidence_ids)
        for graph in graphs.all():
            for node in graph:
                citable.append(node.evidence_ids)
        grounded = sum(1 for ev in citable if ev)
        grounding = Percentage.ratio(grounded, len(citable) or 1)

        mean_conf = (
            sum(dr.confidence.value for dr in dimension_reviews) / len(dimension_reviews)
            if dimension_reviews
            else 0.0
        )
        return ReviewQualityMetrics(
            coverage=coverage, grounding=grounding, confidence=Confidence.clamp(mean_conf)
        )
