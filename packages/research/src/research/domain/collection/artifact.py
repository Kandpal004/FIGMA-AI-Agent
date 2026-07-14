"""Raw artifacts — what a source adapter returns before any structuring.

A :class:`RawArtifact` is a single piece of collected content (an HTML page, a JSON
blob, a document, an image reference) together with its provenance (source id,
locator) and collection timestamp. The engine validates, normalizes, deduplicates,
and then extracts structure from these; the domain never fetches them.

Pure domain: standard library, the shared-kernel error base, research ids, and
shared value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from types import MappingProxyType

from core.errors import DesignDirectorError

from research.domain.shared.ids import ArtifactId, ResearchSourceId
from research.domain.shared.value_objects import ArtifactKind
from research.domain.source.source import SourceLocator

__all__ = ["InvalidArtifactError", "RawArtifact"]


class InvalidArtifactError(DesignDirectorError):
    """Raised when a raw artifact is constructed with invalid data."""

    code = "invalid_artifact"
    http_status = 422


@dataclass(frozen=True, slots=True)
class RawArtifact:
    """A single collected artifact, before structuring.

    Attributes:
        id: Artifact identity.
        source_id: The source it came from.
        kind: The form of the content.
        payload: The raw content (text/HTML/JSON string; a reference for binaries).
        locator: Where in the source it was found.
        collected_at: When it was collected.
        metadata: Provider metadata (read-only); the normalizer adds a content hash.
    """

    id: ArtifactId
    source_id: ResearchSourceId
    kind: ArtifactKind
    payload: str
    locator: SourceLocator
    collected_at: datetime
    metadata: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def is_empty(self) -> bool:
        """Whether the artifact carries no payload."""
        return not self.payload or not self.payload.strip()

    def with_payload(self, payload: str) -> RawArtifact:
        """Return a copy with a normalized payload."""
        return replace(self, payload=payload)

    def with_metadata(self, metadata: Mapping[str, str]) -> RawArtifact:
        """Return a copy with merged metadata (e.g. a content hash)."""
        merged = {**self.metadata, **metadata}
        return replace(self, metadata=MappingProxyType(merged))
