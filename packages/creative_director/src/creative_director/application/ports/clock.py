"""The Clock port — time, injected."""

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
