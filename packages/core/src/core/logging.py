"""Logging configuration.

Provides a single `configure_logging()` entry point plus a `get_logger()`
helper. Supports two formats:

* ``text``  — human-readable, for local development.
* ``json``  — one JSON object per line, for production log aggregation
              (Datadog, Loki, CloudWatch, ...).

The JSON formatter is dependency-free (no structlog) to keep `core` lean, while
still emitting structured, queryable records. Attach ad-hoc structured context
via the standard ``extra=`` kwarg::

    log = get_logger(__name__)
    log.info("run advanced", extra={"run_id": run_id, "to_state": state.value})
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Standard LogRecord attributes we must not duplicate when serializing `extra`.
_RESERVED: frozenset[str] = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    """Serialize a log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Merge any structured context passed via `extra=`.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str, ensure_ascii=False)


_TEXT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(*, level: str = "INFO", fmt: str = "text") -> None:
    """Configure the root logger. Idempotent — safe to call more than once.

    Args:
        level: One of DEBUG, INFO, WARNING, ERROR.
        fmt:   ``"text"`` or ``"json"``.
    """
    handler = logging.StreamHandler(sys.stdout)
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_TEXT_FORMAT))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Tame noisy third-party loggers.
    for noisy in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger. Prefer ``get_logger(__name__)``."""
    return logging.getLogger(name)
