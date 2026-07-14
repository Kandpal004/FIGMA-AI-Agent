"""Research sources — where the engine draws evidence from.

A :class:`SourceLocator` pins *where* in a source to look (a URL plus an optional
selector — a CSS/XPath path, a page number, a video timestamp, an image region). A
:class:`ResearchSource` is a registered source: its kind, the provider (adapter)
that fulfils it, its locator, and a trust weight used in quality scoring.

Pure domain: standard library, the shared-kernel error base, research ids, and
shared value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from research.domain.shared.ids import ResearchSourceId
from research.domain.shared.value_objects import ProviderKind, SourceKind

__all__ = ["InvalidSourceError", "ResearchSource", "SourceLocator"]


class InvalidSourceError(DesignDirectorError):
    """Raised when a source or locator is constructed with invalid data."""

    code = "invalid_research_source"
    http_status = 422


@dataclass(frozen=True, slots=True)
class SourceLocator:
    """Where within a source to look.

    Attributes:
        uri: The primary locator (a URL, file path, or internal reference).
        selector: An optional sub-locator (CSS selector, page number, timestamp,
            image region), as a string.
        extra: Optional structured locator metadata (read-only).
    """

    uri: str
    selector: str = ""
    extra: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.uri or not self.uri.strip():
            raise InvalidSourceError("SourceLocator.uri must be non-empty.")
        if not isinstance(self.extra, MappingProxyType):
            object.__setattr__(self, "extra", MappingProxyType(dict(self.extra)))


@dataclass(frozen=True, slots=True)
class ResearchSource:
    """A registered research source.

    Attributes:
        id: Source identity.
        kind: What kind of source it is.
        provider: The provider (adapter) that fulfils it.
        locator: Where to look.
        name: A human-readable name.
        trust: A trust weight in ``[0, 1]`` used in quality scoring.
        enabled: Whether the source participates in collection.
    """

    id: ResearchSourceId
    kind: SourceKind
    provider: ProviderKind
    locator: SourceLocator
    name: str = ""
    trust: float = 0.7
    enabled: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.trust <= 1.0:
            raise InvalidSourceError(
                "ResearchSource.trust must be within [0, 1].", details={"trust": self.trust}
            )

    @property
    def label(self) -> str:
        """A display label, falling back to the locator uri."""
        return self.name or self.locator.uri
