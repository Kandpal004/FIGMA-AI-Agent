"""RuleBasedReviewPanel — the deterministic critic brain (default review synthesis).

Implements :class:`ReviewPanelPort` by running one deterministic critic per review dimension
over the consolidated evidence. Each critic checks the evidence for the signals its
:class:`DimensionStandard` expects: when they are present it scores the dimension on coverage
and strength; when a critical signal is *absent* it raises a blocking finding naming the
design anti-pattern (a generic layout, weak hierarchy, poor CRO, low trust, or a design with
no business purpose) and demands a fix. This is exactly how the engine rejects
AI-generated-looking work: a polished plan that cites no business, trust, or conversion
grounding fails its critical dimensions.

It is fully deterministic (same input + evidence ⇒ same review), dependency-free, and honest —
it invents no facts; it *judges* the evidence it is given and cites it for every ruling. It is
not an LLM and not a prompt.
"""

from __future__ import annotations

from collections.abc import Sequence

from creative_director.application.contracts import ReviewDraft, ReviewInput
from creative_director.domain.evidence.evidence import CDEvidence, EvidenceGraph
from creative_director.domain.finding.finding import Finding, RequiredChange
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.shared.ids import (
    CDEvidenceId,
    DimensionReviewId,
    FindingId,
    RequiredChangeId,
)
from creative_director.domain.shared.value_objects import (
    Confidence,
    FindingSeverity,
    Priority,
    ProvenanceKind,
    ReviewDimension,
    Score,
    Verdict,
)
from creative_director.infrastructure.adapters.standards import DimensionStandard, standard_for

__all__ = ["RuleBasedReviewPanel"]

_PASS_THRESHOLD = 60.0


class RuleBasedReviewPanel:
    """A deterministic, evidence-grounded implementation of the review panel port."""

    async def review(
        self, review_input: ReviewInput, evidence: EvidenceGraph
    ) -> ReviewDraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        reviews = tuple(
            self._critic(standard_for(dimension), ranked) for dimension in ReviewDimension
        )
        return ReviewDraft(dimension_reviews=reviews)

    # ------------------------------------------------------------------ #
    def _critic(
        self, std: DimensionStandard, ranked: Sequence[CDEvidence]
    ) -> DimensionReview:
        keyword_relevant = [e for e in ranked if self._keyword_match(e, std)]
        provenance_relevant = [e for e in ranked if e.provenance in std.expected]
        relevant = list(dict.fromkeys(keyword_relevant + provenance_relevant))
        # Cite the top evidence of each of the dimension's expected sources, so each ruling is
        # traceable to the upstream engine it judges against (not just the loudest source).
        cite = self._cite(std, keyword_relevant, ranked)
        present = {e.provenance for e in relevant}
        missing = [p for p in std.expected if p not in present]

        findings: list[Finding] = []
        changes: list[RequiredChange] = []

        if std.critical and not keyword_relevant:
            # The critical concern is entirely absent — the tell of a generic, purpose-free
            # (AI/Dribbble) design. Block it.
            score = 22.0
            findings.append(Finding(
                id=FindingId.new(), dimension=std.dimension,
                severity=FindingSeverity.BLOCKING,
                statement=std.concern, anti_pattern=std.anti_pattern, evidence_ids=cite,
            ))
            changes.append(RequiredChange(
                id=RequiredChangeId.new(), dimension=std.dimension, description=std.fix,
                priority=Priority(5), impact=Priority(5), blocking=True, evidence_ids=cite,
            ))
        elif not relevant:
            # A non-critical dimension with no supporting evidence at all — a warning.
            score = 46.0
            findings.append(Finding(
                id=FindingId.new(), dimension=std.dimension,
                severity=FindingSeverity.WARNING,
                statement=std.concern, anti_pattern=std.anti_pattern, evidence_ids=cite,
            ))
            changes.append(RequiredChange(
                id=RequiredChangeId.new(), dimension=std.dimension, description=std.fix,
                priority=Priority(3), impact=Priority(3), blocking=False, evidence_ids=cite,
            ))
        else:
            coverage = (len(std.expected) - len(missing)) / len(std.expected)
            strength = min(len(keyword_relevant), 3)
            score = min(100.0, 40.0 + 35.0 * coverage + 7.0 * strength)
            if missing or not keyword_relevant:
                gap = (
                    ", ".join(p.value for p in missing)
                    if missing
                    else "direct evidence for this concern"
                )
                findings.append(Finding(
                    id=FindingId.new(), dimension=std.dimension,
                    severity=FindingSeverity.WARNING,
                    statement=f"{std.dimension.value} is thinly supported (missing {gap}).",
                    anti_pattern=(std.anti_pattern if not keyword_relevant else None),
                    evidence_ids=cite,
                ))
                changes.append(RequiredChange(
                    id=RequiredChangeId.new(), dimension=std.dimension, description=std.fix,
                    priority=Priority(3), impact=Priority(3), blocking=False, evidence_ids=cite,
                ))

        verdict = Verdict.PASS if score >= _PASS_THRESHOLD else Verdict.FAIL
        if verdict is Verdict.FAIL and not findings:
            findings.append(Finding(
                id=FindingId.new(), dimension=std.dimension,
                severity=FindingSeverity.WARNING,
                statement=f"{std.dimension.value} is below the quality bar.",
                anti_pattern=std.anti_pattern, evidence_ids=cite,
            ))

        return DimensionReview(
            id=DimensionReviewId.new(), dimension=std.dimension, verdict=verdict,
            quality_score=Score.clamp(score), confidence=self._confidence(relevant),
            notes=self._notes(std, score, missing), findings=tuple(findings),
            required_changes=tuple(changes), evidence_ids=cite,
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _keyword_match(evidence: CDEvidence, std: DimensionStandard) -> bool:
        hay = (
            f"{evidence.claim} {evidence.statement} "
            f"{' '.join(t.value for t in evidence.tags)}"
        ).lower()
        return any(k in hay for k in std.keywords)

    @staticmethod
    def _cite(
        std: DimensionStandard,
        keyword_relevant: Sequence[CDEvidence],
        ranked: Sequence[CDEvidence],
    ) -> tuple[CDEvidenceId, ...]:
        # One (highest-confidence) evidence per expected provenance, in expected order.
        top_by_provenance: dict[ProvenanceKind, CDEvidence] = {}
        for e in ranked:
            if e.provenance in std.expected and e.provenance not in top_by_provenance:
                top_by_provenance[e.provenance] = e
        ordered: list[CDEvidence] = [
            top_by_provenance[p] for p in std.expected if p in top_by_provenance
        ]
        ordered.extend(e for e in keyword_relevant if e not in ordered)
        if ordered:
            return tuple(e.id for e in ordered[:2])
        if ranked:
            return (ranked[0].id,)
        return ()

    @staticmethod
    def _confidence(relevant: Sequence[CDEvidence]) -> Confidence:
        return Confidence.clamp(0.5 + 0.1 * min(len(relevant), 5))

    @staticmethod
    def _notes(std: DimensionStandard, score: float, missing: Sequence[ProvenanceKind]) -> str:
        if score >= _PASS_THRESHOLD and not missing:
            return f"{std.dimension.value}: {score:.0f}/100 — grounded and meets the standard."
        if missing:
            names = ", ".join(p.value for p in missing)
            return f"{std.dimension.value}: {score:.0f}/100 — weak; missing {names}. {std.concern}"
        return f"{std.dimension.value}: {score:.0f}/100 — below the bar. {std.concern}"
