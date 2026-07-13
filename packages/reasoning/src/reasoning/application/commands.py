"""Command objects — the Reasoning Engine's typed input contract.

A request to reason is expressed as a :class:`GenerateStrategy` command carrying
the domain :class:`ReasoningRequest` plus the viewer's tenant (for knowledge scope
resolution). Modelling it explicitly keeps the engine's surface stable and
auditable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from reasoning.domain.request.request import ReasoningRequest

__all__ = ["GenerateStrategy"]


@dataclass(frozen=True, slots=True)
class GenerateStrategy:
    """Produce a design strategy for a request.

    Attributes:
        request: What to reason about.
        tenant_id: The viewer's tenant, used to resolve tenant-scoped knowledge
            overrides; ``None`` for the global corpus only.
    """

    request: ReasoningRequest
    tenant_id: uuid.UUID | None = None
