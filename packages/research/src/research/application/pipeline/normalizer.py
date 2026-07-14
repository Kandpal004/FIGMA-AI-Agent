"""Normalizer — stage 4: canonicalize an artifact and stamp a content hash.

Collapses payload whitespace to a canonical form and records a deterministic
``content_hash`` in the artifact's metadata, which the deduplicator uses. Pure and
deterministic (SHA-256 of the normalized payload).
"""

from __future__ import annotations

import hashlib
import re

from research.domain.collection.artifact import RawArtifact

__all__ = ["Normalizer"]

_WHITESPACE = re.compile(r"\s+")


class Normalizer:
    """Canonicalizes raw artifacts and stamps a content hash."""

    def normalize(self, artifact: RawArtifact) -> RawArtifact:
        normalized = _WHITESPACE.sub(" ", artifact.payload).strip()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return artifact.with_payload(normalized).with_metadata({"content_hash": digest})
