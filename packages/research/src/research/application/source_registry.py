"""SourceRegistry — resolves the adapter for each source and artifact.

Stage 1 of the pipeline. Source adapters are registered by :class:`ProviderKind`;
extraction adapters by the :class:`ArtifactKind` s they support (with an optional
default). The engine asks the registry to resolve the right adapter for a given
source or artifact — so adding a provider is a registration, not an engine change.
"""

from __future__ import annotations

from core.errors import DesignDirectorError

from research.application.ports.extraction_port import ExtractionPort
from research.application.ports.source_port import ResearchSourcePort
from research.domain.collection.artifact import RawArtifact
from research.domain.shared.value_objects import ArtifactKind, ProviderKind
from research.domain.source.source import ResearchSource

__all__ = ["SourceRegistry", "UnregisteredProviderError"]


class UnregisteredProviderError(DesignDirectorError):
    """Raised when no adapter is registered for a source's provider or an
    artifact's kind."""

    code = "unregistered_provider"
    http_status = 422


class SourceRegistry:
    """Maps providers → source adapters and artifact kinds → extraction adapters."""

    def __init__(self) -> None:
        self._sources: dict[ProviderKind, ResearchSourcePort] = {}
        self._extractors: dict[ArtifactKind, ExtractionPort] = {}
        self._default_extractor: ExtractionPort | None = None

    def register_source(
        self, provider: ProviderKind, adapter: ResearchSourcePort
    ) -> None:
        """Register a source adapter for a provider."""
        self._sources[provider] = adapter

    def register_extractor(
        self, adapter: ExtractionPort, *, kinds: tuple[ArtifactKind, ...] = (), default: bool = False
    ) -> None:
        """Register an extraction adapter for the artifact kinds it supports."""
        for kind in kinds:
            self._extractors[kind] = adapter
        if default:
            self._default_extractor = adapter

    def resolve_source(self, source: ResearchSource) -> ResearchSourcePort:
        """Return the source adapter for ``source``.

        Raises:
            UnregisteredProviderError: If no adapter is registered.
        """
        adapter = self._sources.get(source.provider)
        if adapter is None:
            raise UnregisteredProviderError(
                f"No source adapter registered for provider {source.provider.value!r}.",
                details={"provider": source.provider.value},
            )
        return adapter

    def resolve_extractor(self, artifact: RawArtifact) -> ExtractionPort:
        """Return the extraction adapter for ``artifact``.

        Raises:
            UnregisteredProviderError: If none is registered and there is no default.
        """
        adapter = self._extractors.get(artifact.kind) or self._default_extractor
        if adapter is None:
            raise UnregisteredProviderError(
                f"No extraction adapter registered for artifact kind {artifact.kind.value!r}.",
                details={"kind": artifact.kind.value},
            )
        return adapter
