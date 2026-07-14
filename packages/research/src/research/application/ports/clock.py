"""Clock port — the application's only source of the current time.

The domain reads no clock; the application obtains "now" solely through this port,
so timestamps (the report's ``created_at``, freshness age) are injected and testable,
and the pipeline stays a pure function of its inputs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

__all__ = ["Clock"]


@runtime_checkable
class Clock(Protocol):
    """A source of the current time (timezone-aware, UTC)."""

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC datetime."""
        ...
