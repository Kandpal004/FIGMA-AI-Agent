"""Brand language rules — the grammar the brand writes by (never copy).

:class:`BrandLanguageRules` states the person, terminology, capitalisation stance, and
the words to prefer and forbid — the rules that make every future sentence sound like
the brand. It writes no sentences. Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["BrandLanguageRules", "InvalidLanguageError"]


class InvalidLanguageError(DesignDirectorError):
    """Raised when language rules are constructed with invalid data."""

    code = "invalid_language_rules"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandLanguageRules:
    """The cited grammar the brand writes by.

    Attributes:
        person: The grammatical person/address (e.g. "second person, we→you").
        capitalization: The capitalisation stance (e.g. "sentence case").
        terminology: Canonical term → preferred usage (read-only).
        preferred_words: Words the brand favours.
        forbidden_words: Words the brand never uses.
        principles: Language principles to honour.
        evidence_ids: The evidence supporting it.
    """

    person: str = ""
    capitalization: str = ""
    terminology: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    preferred_words: tuple[str, ...] = ()
    forbidden_words: tuple[str, ...] = ()
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.terminology, MappingProxyType):
            object.__setattr__(self, "terminology", MappingProxyType(dict(self.terminology)))
        object.__setattr__(self, "preferred_words", tuple(self.preferred_words))
        object.__setattr__(self, "forbidden_words", tuple(self.forbidden_words))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
