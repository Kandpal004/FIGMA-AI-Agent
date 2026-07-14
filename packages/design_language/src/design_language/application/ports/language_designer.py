"""The Language Designer port — the designer brain.

Given the assembled input and the consolidated evidence, an implementation designs the visual
language: the Visual DNA, the selected language archetype (with considered alternatives), the
eleven philosophies, the four personalities, the token system, and the grid and responsive
systems — grounded by citing evidence ids. The engine owns everything downstream — validating
grounding, deriving the rules/graphs/explanation, scoring, and assembling the versioned
specification.

The default implementation is the deterministic rule-based designer in the infrastructure
layer; this port lets it be swapped (e.g. for an LLM-backed designer) without the engine
changing. An implementation must cite only supplied evidence — it invents no facts; it
*composes* a language over the evidence it is given.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from design_language.application.contracts import LanguageDraft, LanguageInput
from design_language.domain.evidence.evidence import EvidenceGraph

__all__ = ["LanguageDesignerPort"]


@runtime_checkable
class LanguageDesignerPort(Protocol):
    """Designs the visual language from input and evidence."""

    async def design(
        self, language_input: LanguageInput, evidence: EvidenceGraph
    ) -> LanguageDraft:
        """Return a cited language draft (awaiting rules, graphs, and assembly)."""
        ...
