"""The ResearchEngine — the orchestrator of the acquisition pipeline.

Given a request, it runs the full pipeline in fixed order — collect → validate →
normalize → deduplicate → extract evidence → extract entities → detect relationships
→ map to knowledge → assemble — producing a single, provenance-tracked, immutable,
versioned :class:`ResearchReport`. It NEVER generates designs, UI, or decisions; its
sole job is high-quality evidence.

The pipeline is deterministic apart from the two provider ports (collection and
extraction). Quality, freshness, and completeness are computed by explicit formulas.
Because the report validates provenance integrity at construction, an unattributed
finding or a dangling edge cannot be produced. Every collaborator is injected, so
the engine is framework-independent and testable with fakes.
"""

from __future__ import annotations

from datetime import datetime

from research.application.commands import Research
from research.application.pipeline.collector import Collector
from research.application.pipeline.deduplicator import Deduplicator
from research.application.pipeline.entity_extractor import EntityExtractor
from research.application.pipeline.evidence_extractor import EvidenceExtractor
from research.application.pipeline.knowledge_mapper import KnowledgeMapper
from research.application.pipeline.normalizer import Normalizer
from research.application.pipeline.relationship_detector import RelationshipDetector
from research.application.pipeline.validator import Validator
from research.application.ports.clock import Clock
from research.application.ports.knowledge_link import KnowledgeLinkPort
from research.application.ports.unit_of_work import UnitOfWorkFactory
from research.application.source_registry import SourceRegistry
from research.domain.collection.artifact import RawArtifact
from research.domain.entity.graph import EntityGraph
from research.domain.evidence.evidence import Evidence, EvidenceGraph
from research.domain.report.report import ResearchReport
from research.domain.result.quality import QualityMetrics
from research.domain.result.result import ResearchResult
from research.domain.shared.ids import (
    ResearchReportId,
    ResearchReportLineageId,
    ResearchResultId,
)
from research.domain.shared.value_objects import (
    Completeness,
    Confidence,
    Freshness,
    QualityScore,
    ResearchCategory,
    SourceKind,
)
from research.domain.source.source import ResearchSource

__all__ = ["ResearchEngine"]

# Quality-scoring weights (sum to 1.0) and the per-warning penalty.
_W_CONFIDENCE = 0.4
_W_COMPLETENESS = 0.2
_W_FRESHNESS = 0.2
_W_TRUST = 0.2
_WARN_PENALTY = 5.0

_SOURCE_CATEGORY: dict[SourceKind, ResearchCategory] = {
    SourceKind.BUSINESS_WEBSITE: ResearchCategory.WEBSITE,
    SourceKind.COMPETITOR_WEBSITE: ResearchCategory.COMPETITOR,
    SourceKind.BRAND_GUIDELINES: ResearchCategory.BRAND,
    SourceKind.DESIGN_SYSTEM: ResearchCategory.DESIGN,
    SourceKind.KNOWLEDGE_ENGINE: ResearchCategory.KNOWLEDGE,
    SourceKind.PROJECT_MEMORY: ResearchCategory.MEMORY,
    SourceKind.USER_DOCUMENT: ResearchCategory.DOCUMENT,
    SourceKind.PDF: ResearchCategory.DOCUMENT,
    SourceKind.IMAGE: ResearchCategory.IMAGE,
    SourceKind.VIDEO: ResearchCategory.VIDEO,
    SourceKind.BROWSER_SESSION: ResearchCategory.WEBSITE,
}


class ResearchEngine:
    """Runs the acquisition pipeline and persists a research report."""

    def __init__(
        self,
        *,
        registry: SourceRegistry,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
        knowledge_link: KnowledgeLinkPort | None = None,
        collector: Collector | None = None,
        validator: Validator | None = None,
        normalizer: Normalizer | None = None,
        deduplicator: Deduplicator | None = None,
        evidence_extractor: EvidenceExtractor | None = None,
        entity_extractor: EntityExtractor | None = None,
        relationship_detector: RelationshipDetector | None = None,
        knowledge_mapper: KnowledgeMapper | None = None,
    ) -> None:
        self._registry = registry
        self._uow = unit_of_work_factory
        self._clock = clock
        self._knowledge_link = knowledge_link
        self._collector = collector or Collector()
        self._validator = validator or Validator()
        self._normalizer = normalizer or Normalizer()
        self._deduplicator = deduplicator or Deduplicator()
        self._evidence = evidence_extractor or EvidenceExtractor()
        self._entities = entity_extractor or EntityExtractor()
        self._relationships = relationship_detector or RelationshipDetector()
        self._mapper = knowledge_mapper or KnowledgeMapper()

    async def research(self, command: Research) -> ResearchReport:
        """Run the full pipeline and persist the resulting report."""
        request = command.request
        now = self._clock.now()
        source_by_id = {s.id: s for s in request.sources}

        # 1. Collect.
        artifacts = await self._collector.collect(
            request.enabled_sources(), self._registry.resolve_source
        )

        # 2-4. Validate (drop ERRORs), normalize; carry the source + outcome.
        prepared: list[tuple[RawArtifact, ResearchSource, object]] = []
        for artifact in artifacts:
            source = source_by_id[artifact.source_id]
            outcome = self._validator.validate(artifact, source)
            if not outcome.is_valid:
                continue
            normalized = self._normalizer.normalize(artifact)
            prepared.append((normalized, source, outcome))

        # 5. Deduplicate.
        kept_ids = {a.id for a in self._deduplicator.dedupe([p[0] for p in prepared])}
        prepared = [p for p in prepared if p[0].id in kept_ids]

        # 6-9 + assembly, per artifact.
        results: list[ResearchResult] = []
        all_evidence: list[Evidence] = []
        all_entities = []
        all_relationships = []
        metrics_parts: list[QualityMetrics] = []

        for artifact, source, outcome in prepared:
            extractor = self._registry.resolve_extractor(artifact)
            extraction = await extractor.extract(artifact)

            evidence = self._evidence.extract(artifact, source, extraction)
            evidence = await self._mapper.map(
                evidence, self._knowledge_link, tenant_id=request.tenant_id
            )
            entities = self._entities.extract(artifact, source, extraction, evidence)
            relationships = self._relationships.detect(entities, extraction, evidence)

            metrics = self._score(source, artifact, evidence, entities, relationships, outcome, now)
            results.append(
                ResearchResult(
                    id=ResearchResultId.new(),
                    source_id=source.id,
                    timestamp=artifact.collected_at,
                    category=_SOURCE_CATEGORY.get(source.kind, ResearchCategory.WEBSITE),
                    metrics=metrics,
                    version=1,
                    evidence=evidence,
                    entities=entities,
                    relationships=relationships,
                    tags=frozenset(request.tags),
                    issues=outcome.issues,  # type: ignore[attr-defined]
                )
            )
            all_evidence.extend(evidence)
            all_entities.extend(entities)
            all_relationships.extend(relationships)
            metrics_parts.append(metrics)

        report = ResearchReport(
            id=ResearchReportId.new(),
            lineage_id=command.lineage_id or ResearchReportLineageId.new(),
            version=await self._next_version(command.lineage_id),
            project_id=request.project_id,
            goal=request.goal,
            results=tuple(results),
            evidence_graph=EvidenceGraph.of(all_evidence),
            entity_graph=EntityGraph.of(all_entities, all_relationships),
            quality=QualityMetrics.aggregate(metrics_parts),
            created_at=now,
        )

        async with self._uow() as uow:
            await uow.reports.save(report)
            await uow.commit()
        return report

    # ------------------------------------------------------------------ #
    def _score(
        self,
        source: ResearchSource,
        artifact: RawArtifact,
        evidence,
        entities,
        relationships,
        outcome,
        now: datetime,
    ) -> QualityMetrics:
        confidences = [e.confidence.value for e in evidence] + [e.confidence.value for e in entities]
        confidence = sum(confidences) / len(confidences) if confidences else 0.0
        present = sum(1 for group in (evidence, entities, relationships) if group)
        completeness = Completeness.from_counts(present, 3)
        age_days = max(0.0, (now - artifact.collected_at).total_seconds() / 86400.0)
        freshness = Freshness.from_age(age_days)
        raw = (
            _W_CONFIDENCE * confidence * 100
            + _W_COMPLETENESS * completeness.value * 100
            + _W_FRESHNESS * freshness.value * 100
            + _W_TRUST * source.trust * 100
        )
        penalty = _WARN_PENALTY * len(outcome.warnings())  # type: ignore[attr-defined]
        return QualityMetrics(
            quality_score=QualityScore.clamp(raw - penalty),
            freshness=freshness,
            completeness=completeness,
            confidence=Confidence.clamp(confidence),
        )

    async def _next_version(self, lineage_id: ResearchReportLineageId | None) -> int:
        if lineage_id is None:
            return 1
        async with self._uow() as uow:
            history = await uow.reports.history(lineage_id)
        return len(history) + 1
