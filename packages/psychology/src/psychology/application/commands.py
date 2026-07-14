"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from psychology.application.request import PsychologyRequest
from psychology.domain.shared.ids import PsychologyReportLineageId

__all__ = ["BuildPsychology"]


@dataclass(frozen=True, slots=True)
class BuildPsychology:
    """Build a customer psychology model for a request.

    Attributes:
        request: What to model.
        lineage_id: The report lineage to append a new version to; ``None`` starts a
            fresh lineage.
    """

    request: PsychologyRequest
    lineage_id: PsychologyReportLineageId | None = None
