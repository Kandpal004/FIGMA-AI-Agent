"""The DimensionReview — the Creative Director's verdict on one review dimension.

A :class:`DimensionReview` is the engine's ruling on a single one of the sixteen dimensions
(business alignment, conversion strategy, trust signals, typography direction, …): a pass/fail
verdict, a 0–100 quality score, a confidence, review notes, and the findings and required
changes it raises. It is the unit the scorer rolls up into category scores and the approval
evaluator inspects for blockers.

Pure domain: standard library, the shared-kernel error base, CD ids, and the finding models.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from creative_director.domain.finding.finding import Finding, RequiredChange
from creative_director.domain.shared.ids import CDEvidenceId, DimensionReviewId
from creative_director.domain.shared.value_objects import (
    AntiPattern,
    Confidence,
    FindingSeverity,
    ReviewDimension,
    Score,
    Verdict,
)

__all__ = ["DimensionReview", "InvalidDimensionReviewError"]


class InvalidDimensionReviewError(DesignDirectorError):
    """Raised when a dimension review is constructed with invalid data."""

    code = "invalid_creative_director_dimension_review"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DimensionReview:
    """The Creative Director's ruling on one dimension.

    Attributes:
        id: Review identity.
        dimension: The dimension reviewed.
        verdict: Pass or fail.
        quality_score: The dimension's 0–100 quality.
        confidence: Confidence in the verdict.
        notes: The reviewer's rationale.
        findings: The findings raised (blocking / warning / recommendation).
        required_changes: The concrete changes demanded.
        evidence_ids: The evidence grounding the dimension-level verdict.
    """

    id: DimensionReviewId
    dimension: ReviewDimension
    verdict: Verdict
    quality_score: Score
    confidence: Confidence
    notes: str
    findings: tuple[Finding, ...] = ()
    required_changes: tuple[RequiredChange, ...] = ()
    evidence_ids: tuple[CDEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.notes or not self.notes.strip():
            raise InvalidDimensionReviewError("DimensionReview.notes must be non-empty.")
        for finding in self.findings:
            if finding.dimension is not self.dimension:
                raise InvalidDimensionReviewError(
                    "A finding's dimension must match the review's dimension.",
                    details={"dimension": self.dimension.value},
                )
        if self.verdict is Verdict.FAIL and not self.findings:
            raise InvalidDimensionReviewError(
                "A failing dimension review must carry at least one finding.",
                details={"dimension": self.dimension.value},
            )
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "required_changes", tuple(self.required_changes))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    # -- queries ----------------------------------------------------------- #
    def blocking_findings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is FindingSeverity.BLOCKING)

    def warnings(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is FindingSeverity.WARNING)

    def recommendations(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity is FindingSeverity.RECOMMENDATION)

    def anti_patterns(self) -> tuple[AntiPattern, ...]:
        return tuple(dict.fromkeys(f.anti_pattern for f in self.findings if f.anti_pattern))

    @property
    def is_pass(self) -> bool:
        return self.verdict is Verdict.PASS

    @property
    def has_blocker(self) -> bool:
        return bool(self.blocking_findings())

    def all_evidence_ids(self) -> tuple[CDEvidenceId, ...]:
        ids: list[CDEvidenceId] = list(self.evidence_ids)
        for finding in self.findings:
            ids.extend(finding.all_evidence_ids())
        for change in self.required_changes:
            ids.extend(change.all_evidence_ids())
        return tuple(ids)
