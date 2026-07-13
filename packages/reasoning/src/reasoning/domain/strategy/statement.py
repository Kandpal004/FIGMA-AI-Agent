"""EvidencedStatement — the atomic, cited unit every strategy point is made of.

A strategy answer is never bare prose. It is an :class:`EvidencedStatement`: a
statement, the evidence that backs it (at least one citation, always), the reason
that produced it, and its confidence. Because every point across every section is
this same value object, the "≥1 citation" invariant is enforced in exactly one
place — here, at construction — and cannot be bypassed.

When the corpus has nothing to support a point, the engine does *not* fabricate an
:class:`EvidencedStatement`; it records a
:class:`~reasoning.domain.strategy.gap.KnowledgeGap` instead. The two are mutually
exclusive by design: a statement is always grounded; a gap is always the explicit
absence of grounding.

Pure domain: standard library, the shared-kernel error base, and reasoning ids.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from reasoning.domain.shared.ids import EvidenceId, ReasonNodeId
from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = ["EvidencedStatement", "InvalidStatementError"]


class InvalidStatementError(DesignDirectorError):
    """Raised when an evidenced statement is constructed without grounding."""

    code = "invalid_statement"
    http_status = 422


@dataclass(frozen=True, slots=True)
class EvidencedStatement:
    """A single cited strategy claim.

    Attributes:
        dimension: The strategy dimension this claim belongs to.
        statement: The claim itself (a direction, never a design).
        evidence_ids: The evidence backing the claim (must be non-empty).
        confidence: Confidence in the claim, in ``[0, 1]``.
        reason_id: The reason node that produced the claim, if any.
    """

    dimension: ReasoningDimension
    statement: str
    evidence_ids: tuple[EvidenceId, ...]
    confidence: float
    reason_id: ReasonNodeId | None = None

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidStatementError("EvidencedStatement.statement must be non-empty.")
        normalized = tuple(self.evidence_ids)
        if not normalized:
            raise InvalidStatementError(
                "An EvidencedStatement must cite at least one piece of evidence "
                "(no uncited claims). Use a KnowledgeGap when the corpus is silent.",
                details={"statement": self.statement},
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidStatementError(
                "EvidencedStatement.confidence must be within [0, 1].",
                details={"confidence": self.confidence},
            )
        object.__setattr__(self, "evidence_ids", normalized)
