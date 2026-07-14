"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from design_language.application.request import DesignLanguageRequest
from design_language.domain.shared.ids import DesignLanguageSpecLineageId

__all__ = ["BuildDesignLanguage"]


@dataclass(frozen=True, slots=True)
class BuildDesignLanguage:
    """Build a design-language specification for a request.

    Attributes:
        request: What to define a visual language for.
        lineage_id: The specification lineage to append a new version to; ``None`` starts a
            fresh lineage.
    """

    request: DesignLanguageRequest
    lineage_id: DesignLanguageSpecLineageId | None = None
