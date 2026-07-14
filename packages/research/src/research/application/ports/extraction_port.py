"""The Extraction port — the engine's door to structuring raw artifacts.

An :class:`ExtractionPort` adapter turns a :class:`RawArtifact` into a
:class:`RawExtraction` (candidate entities/evidence/relationships). A deterministic
parser fulfils this today; vision and LLM extractors (via OpenRouter) are future
adapters behind this same interface. Because extraction is a *separate* port from
collection, the extraction strategy can be swapped without touching any source
adapter — all provider intelligence stays here, out of the domain.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from research.domain.collection.artifact import RawArtifact
from research.domain.collection.extraction import RawExtraction
from research.domain.shared.value_objects import ArtifactKind

__all__ = ["ExtractionPort"]


@runtime_checkable
class ExtractionPort(Protocol):
    """Structures a raw artifact into extraction candidates."""

    def supports(self, kind: ArtifactKind) -> bool:
        """Whether this extractor can handle the given artifact kind."""
        ...

    async def extract(self, artifact: RawArtifact) -> RawExtraction:
        """Return the candidate entities/evidence/relationships for ``artifact``."""
        ...
