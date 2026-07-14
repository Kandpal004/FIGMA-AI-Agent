"""The Clock port — time, injected.

The domain and application never call ``datetime.now`` directly; they ask an injected
clock, so time is deterministic under test and centralised in one adapter.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

__all__ = ["Clock"]


@runtime_checkable
class Clock(Protocol):
    """Supplies the current time."""

    def now(self) -> datetime:
        """Return the current time (timezone-aware, UTC)."""
        ...
