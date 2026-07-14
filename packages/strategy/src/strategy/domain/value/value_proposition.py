"""The value proposition — the promise the brand makes.

A :class:`ValueProposition` states the headline promise, the primary benefit, the
differentiators that make it credible, and the proof points that back it — tied to the
jobs-to-be-done it serves and grounded in evidence.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import JobToBeDoneId, StrategyEvidenceId

__all__ = ["InvalidValuePropositionError", "ValueProposition"]


class InvalidValuePropositionError(DesignDirectorError):
    """Raised when a value proposition is constructed with invalid data."""

    code = "invalid_value_proposition"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ValueProposition:
    """The cited promise the brand makes to its customer.

    Attributes:
        headline_promise: The single, central promise.
        primary_benefit: The primary benefit delivered.
        differentiators: What makes the promise distinct.
        proof_points: The evidence-backed proof of the promise.
        target_jtbd_ids: The jobs-to-be-done this proposition serves.
        evidence_ids: The evidence supporting it.
    """

    headline_promise: str
    primary_benefit: str
    differentiators: tuple[str, ...] = ()
    proof_points: tuple[str, ...] = ()
    target_jtbd_ids: tuple[JobToBeDoneId, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.headline_promise or not self.headline_promise.strip():
            raise InvalidValuePropositionError(
                "ValueProposition.headline_promise must be non-empty."
            )
        if not self.primary_benefit or not self.primary_benefit.strip():
            raise InvalidValuePropositionError(
                "ValueProposition.primary_benefit must be non-empty."
            )
        object.__setattr__(self, "differentiators", tuple(self.differentiators))
        object.__setattr__(self, "proof_points", tuple(self.proof_points))
        object.__setattr__(self, "target_jtbd_ids", tuple(self.target_jtbd_ids))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
