"""Developer notes, comments, and annotations — the handoff layer carried on nodes.

A senior designer's file is not just visuals: it carries developer notes (spacing intent, states,
data bindings), design comments, and measurement annotations that Figma's Dev Mode surfaces to
engineers. Modelling these on the node means the handoff survives into the Figma Design Model and
a future Dev-Mode renderer can emit them directly.

Pure domain: standard library and the shared-kernel error base.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

__all__ = ["Annotation", "Comment", "DeveloperNote", "InvalidAnnotationError"]


class InvalidAnnotationError(DesignDirectorError):
    """Raised when an annotation is constructed with invalid data."""

    code = "invalid_figma_design_annotation"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DeveloperNote:
    """A note for engineers, surfaced in Dev Mode.

    Attributes:
        label: A short label (e.g. "State", "Data", "Behaviour").
        body: The note body.
    """

    label: str
    body: str

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidAnnotationError("DeveloperNote.label must be non-empty.")
        if not self.body or not self.body.strip():
            raise InvalidAnnotationError("DeveloperNote.body must be non-empty.")
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(self, "body", self.body.strip())


@dataclass(frozen=True, slots=True)
class Comment:
    """A design comment pinned to a node.

    Attributes:
        author: A human-readable author label.
        body: The comment body.
    """

    author: str
    body: str

    def __post_init__(self) -> None:
        if not self.body or not self.body.strip():
            raise InvalidAnnotationError("Comment.body must be non-empty.")
        object.__setattr__(self, "author", (self.author or "").strip())
        object.__setattr__(self, "body", self.body.strip())


@dataclass(frozen=True, slots=True)
class Annotation:
    """A measurement / spec annotation surfaced in Dev Mode.

    Attributes:
        property: The property annotated (e.g. "spacing", "width", "color").
        value: The annotated value or token reference.
    """

    property: str
    value: str

    def __post_init__(self) -> None:
        if not self.property or not self.property.strip():
            raise InvalidAnnotationError("Annotation.property must be non-empty.")
        if not self.value or not self.value.strip():
            raise InvalidAnnotationError("Annotation.value must be non-empty.")
        object.__setattr__(self, "property", self.property.strip())
        object.__setattr__(self, "value", self.value.strip())
