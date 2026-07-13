"""Clock port — the application's only source of the current time.

The domain reads no clock; the application obtains "now" solely through this port
so timestamps (an entry's ``created_at``/``updated_at``) are deterministic and
testable.
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
