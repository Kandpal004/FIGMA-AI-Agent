"""The embedding port — the future vectorization seam.

When semantic search (Qdrant) is introduced, entries must be turned into vectors
by *some* embedding model. This port isolates that dependency: the application and
domain never import an embedding SDK; an infrastructure adapter implements this
interface, and the search/indexing machinery depends only on the protocol.

No implementation ships in this phase — this defines the seam so that adding
embeddings later (behind :class:`EmbeddingPort`) requires no change to the core.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

__all__ = ["EmbeddingPort"]


@runtime_checkable
class EmbeddingPort(Protocol):
    """Turns text into dense vectors for semantic indexing/search."""

    async def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Return one embedding vector per input text, in order."""
        ...

    @property
    def dimensions(self) -> int:
        """The dimensionality of the vectors this embedder produces."""
        ...
