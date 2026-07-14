"""The Block model — the typed content units a section lays out.

A :class:`Block` is one planning-level building unit inside a section: a content block, a
media block, a trust block, a CTA block, a product block, a recommendation block, an FAQ
block, a review block, or a footer block (the spec's block taxonomy, :class:`BlockKind`). A
block declares *what* must appear and *what data it needs* — never how it looks. Blocks are
the leaves of the Content Graph.

Pure domain: standard library, the shared-kernel error base, wireframe ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.shared.ids import BlockId, WFEvidenceId
from wireframe.domain.shared.value_objects import BlockKind, DataKind, Priority

__all__ = ["Block", "InvalidBlockError"]


class InvalidBlockError(DesignDirectorError):
    """Raised when a block is constructed with invalid data."""

    code = "invalid_wireframe_block"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Block:
    """One typed block a section must lay out.

    Attributes:
        id: Block identity.
        kind: The block taxonomy kind (content/media/trust/cta/product/…).
        label: A short planning label for the block's role.
        priority: Its priority within the section (5 = highest).
        is_required: Whether the block is required in the section.
        data_kinds: The kinds of data the block needs supplied.
        evidence_ids: The evidence grounding the block.
    """

    id: BlockId
    kind: BlockKind
    label: str
    priority: Priority = Priority(3)
    is_required: bool = True
    data_kinds: tuple[DataKind, ...] = ()
    evidence_ids: tuple[WFEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidBlockError("Block.label must be non-empty.")
        object.__setattr__(self, "data_kinds", tuple(dict.fromkeys(self.data_kinds)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        return self.evidence_ids
