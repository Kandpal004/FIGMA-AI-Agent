"""Validator — stage 3: validate each artifact deterministically.

Runs a small set of composable rules over an artifact and its source, producing a
:class:`ValidationOutcome`. An empty payload is an ``ERROR`` (the artifact is
rejected); a thin payload or a low-trust source is a ``WARN`` (kept, but its quality
score is penalised). Issues are retained on the result for auditability.
"""

from __future__ import annotations

from research.domain.collection.artifact import RawArtifact
from research.domain.source.source import ResearchSource
from research.domain.validation.issue import IssueSeverity, ValidationIssue, ValidationOutcome

__all__ = ["Validator"]

_THIN_PAYLOAD_CHARS = 20
_LOW_TRUST = 0.4


class Validator:
    """Validates raw artifacts against deterministic rules."""

    def validate(self, artifact: RawArtifact, source: ResearchSource) -> ValidationOutcome:
        issues: list[ValidationIssue] = []

        if artifact.is_empty:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.ERROR, code="empty_payload",
                    message="Artifact has no payload.", field="payload",
                )
            )
        elif len(artifact.payload.strip()) < _THIN_PAYLOAD_CHARS:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.WARN, code="thin_payload",
                    message="Artifact payload is very short.", field="payload",
                )
            )

        if source.trust < _LOW_TRUST:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.WARN, code="low_trust",
                    message=f"Source trust {source.trust:.2f} is below the reliable threshold.",
                    field="trust",
                )
            )

        return ValidationOutcome(issues=tuple(issues))
