"""KnowledgeMapper — stage 9: link evidence to the Knowledge Engine.

For each piece of evidence, asks the :class:`KnowledgeLinkPort` whether it
corresponds to a known principle; if so, links the evidence to that entry (attaching
its lineage id). Linking is optional — evidence with no match passes through
unchanged. This is the seam that connects freshly-researched evidence to the
platform's curated knowledge.
"""

from __future__ import annotations

from collections.abc import Sequence

from research.application.ports.knowledge_link import KnowledgeLinkPort
from research.domain.evidence.evidence import Evidence

__all__ = ["KnowledgeMapper"]


class KnowledgeMapper:
    """Links research evidence to Knowledge-Engine entries where they correspond."""

    async def map(
        self,
        evidence: Sequence[Evidence],
        knowledge_link: KnowledgeLinkPort | None,
        *,
        tenant_id: object | None = None,
    ) -> tuple[Evidence, ...]:
        if knowledge_link is None:
            return tuple(evidence)

        mapped: list[Evidence] = []
        for item in evidence:
            links = await knowledge_link.link(
                item.claim, item.category, tenant_id=tenant_id, limit=1
            )
            if links:
                mapped.append(item.with_knowledge(links[0].knowledge_id))
            else:
                mapped.append(item)
        return tuple(mapped)
