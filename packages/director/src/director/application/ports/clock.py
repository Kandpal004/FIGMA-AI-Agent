"""Clock port — the application's only source of "now".

The domain never reads a clock, and the application must not call
``datetime.now()`` directly either: ambient time makes behaviour
non-deterministic and untestable. Instead, anything that needs the current time
(stamping a decision, an event) depends on this :class:`Clock` port, and tests
inject a fixed clock for exact, repeatable assertions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

__all__ = ["Clock"]


@runtime_checkable
class Clock(Protocol):
    """A source of the current time.

    Implementations must return a timezone-aware :class:`~datetime.datetime`
    (UTC), so timestamps are unambiguous across processes and storage.
    """

    def now(self) -> datetime:
        """Return the current instant as a timezone-aware UTC datetime."""
        ...
