"""Deduplicator — stage 5: drop duplicate artifacts.

Removes artifacts that share a ``(source, content_hash)`` key (the hash stamped by
the normalizer), keeping the first occurrence. Deterministic; preserves order.
"""

from __future__ import annotations

from collections.abc import Sequence

from research.domain.collection.artifact import RawArtifact

__all__ = ["Deduplicator"]


class Deduplicator:
    """De-duplicates normalized artifacts by source and content hash."""

    def dedupe(self, artifacts: Sequence[RawArtifact]) -> tuple[RawArtifact, ...]:
        seen: set[tuple[str, str]] = set()
        kept: list[RawArtifact] = []
        for artifact in artifacts:
            key = (str(artifact.source_id), artifact.metadata.get("content_hash", artifact.payload))
            if key in seen:
                continue
            seen.add(key)
            kept.append(artifact)
        return tuple(kept)
