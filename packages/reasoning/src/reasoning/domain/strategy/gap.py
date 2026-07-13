"""KnowledgeGap — the explicit record of "the corpus had nothing to say".

Determinism and honesty require that when the Knowledge Engine returns no
applicable principle for a dimension, the Reasoning Engine records the absence
rather than inventing an answer. A :class:`KnowledgeGap` is that record: a
first-class, reportable statement that a strategy dimension is *ungrounded*, so it
lowers confidence and is surfaced to the Creative Director for authoring — never
silently filled.

Pure domain: standard library, the shared-kernel error base, and shared enums.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = ["InvalidKnowledgeGapError", "KnowledgeGap"]


class InvalidKnowledgeGapError(DesignDirectorError):
    """Raised when a knowledge gap is constructed with invalid data."""

    code = "invalid_knowledge_gap"
    http_status = 422


@dataclass(frozen=True, slots=True)
class KnowledgeGap:
    """A dimension for which no supporting knowledge was found.

    Attributes:
        dimension: The dimension left ungrounded.
        question: The strategic question that could not be answered from the corpus.
        detail: What was sought and why the gap matters.
        suggested_action: A concrete remediation (e.g. "author knowledge for X" or
            "escalate to the Creative Director").
    """

    dimension: ReasoningDimension
    question: str
    detail: str = ""
    suggested_action: str = "Escalate to the Creative Director for authoring."

    def __post_init__(self) -> None:
        if not self.question or not self.question.strip():
            raise InvalidKnowledgeGapError("KnowledgeGap.question must be non-empty.")
