"""Discovery — search, filtering, and sorting strategy.

:class:`SearchStrategy`, :class:`FilteringStrategy`, and :class:`SortingStrategy` define how
shoppers find products: the search scope and no-results handling, the faceted-navigation
filters, and the sort options and default. :class:`Discovery` groups them. All cited.

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.shared.ids import IAEvidenceId
from ia.domain.shared.value_objects import FilterType, SortOption

__all__ = [
    "Discovery",
    "FilteringStrategy",
    "InvalidDiscoveryError",
    "SearchStrategy",
    "SortingStrategy",
]


class InvalidDiscoveryError(DesignDirectorError):
    """Raised when a discovery strategy is constructed with invalid data."""

    code = "invalid_discovery"
    http_status = 422


@dataclass(frozen=True, slots=True)
class SearchStrategy:
    """The cited search strategy.

    Attributes:
        scope: What search covers (e.g. "products, collections, content").
        autocomplete: Whether autocomplete/typeahead is used.
        no_results_handling: How zero-result searches are handled.
        principles: Search principles to honour.
        evidence_ids: The evidence supporting it.
    """

    scope: str = "products"
    autocomplete: bool = True
    no_results_handling: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class FilteringStrategy:
    """The cited faceted-filtering strategy.

    Attributes:
        facets: The filter facets to expose.
        principles: Filtering principles to honour.
        evidence_ids: The evidence supporting it.
    """

    facets: tuple[FilterType, ...] = ()
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "facets", tuple(dict.fromkeys(self.facets)))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class SortingStrategy:
    """The cited sorting strategy.

    Attributes:
        options: The available sort options.
        default: The default sort option.
        evidence_ids: The evidence supporting it.
    """

    options: tuple[SortOption, ...] = ()
    default: SortOption = SortOption.RELEVANCE
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        options = tuple(dict.fromkeys(self.options))
        if options and self.default not in options:
            raise InvalidDiscoveryError(
                "SortingStrategy.default must be one of the options.",
                details={"default": self.default.value},
            )
        object.__setattr__(self, "options", options)
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class Discovery:
    """The consolidated, cited product-discovery strategy."""

    search: SearchStrategy = SearchStrategy()
    filtering: FilteringStrategy = FilteringStrategy()
    sorting: SortingStrategy = SortingStrategy()

    def evidence_ids(self) -> tuple[IAEvidenceId, ...]:
        return (
            *self.search.evidence_ids,
            *self.filtering.evidence_ids,
            *self.sorting.evidence_ids,
        )
