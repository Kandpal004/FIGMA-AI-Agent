"""ContextAdapter — bridges the reasoning engine to Phase-2 project memory.

Implements the reasoning-owned :class:`ContextPort` over the Phase-2 Memory
Engine: it loads a project's memory records and projects them into the decoupled
:class:`BrandContext` and :class:`ContextFact` value objects the reasoner reads.
The reasoning application never imports Phase 2; this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from director.application.memory.memory_engine import MemoryEngine
from director.domain.memory.entities import MemoryKind
from director.domain.shared.ids import ProjectId, SectionId

from reasoning.domain.request.request import BrandContext, ContextFact

__all__ = ["ContextAdapter"]

# Memory kinds that describe the brand (folded into BrandContext).
_BRAND_KINDS = {
    MemoryKind.BRAND_VOICE,
    MemoryKind.BRAND_COLOR,
    MemoryKind.TYPOGRAPHY,
    MemoryKind.DESIGN_TOKEN,
}


class ContextAdapter:
    """Implements :class:`ContextPort` over the Phase-2 Memory Engine."""

    def __init__(self, memory: MemoryEngine) -> None:
        self._memory = memory

    async def load_brand(
        self, project_id: str, *, tenant_id: object | None = None
    ) -> BrandContext:
        context = await self._memory.load_context(ProjectId.from_string(project_id))
        voice = ""
        values: list[str] = []
        attributes: dict[str, str] = {}
        for record in context.records:
            if record.kind is MemoryKind.BRAND_VOICE and not voice:
                voice = record.body
            elif record.kind in _BRAND_KINDS:
                attributes[record.title or record.kind.value] = record.body
        return BrandContext(voice=voice, values=tuple(values), attributes=attributes)

    async def load_memory_facts(
        self,
        project_id: str,
        *,
        section_id: str | None = None,
        tenant_id: object | None = None,
    ) -> Sequence[ContextFact]:
        section = SectionId.from_string(section_id) if section_id else None
        context = await self._memory.load_context(
            ProjectId.from_string(project_id), section_id=section
        )
        return tuple(
            ContextFact(kind=record.kind.value, statement=record.body)
            for record in context.records
        )
