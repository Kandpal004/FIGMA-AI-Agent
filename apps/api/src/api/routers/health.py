"""Health and readiness endpoints.

* ``GET /health``  — liveness. Cheap; always 200 if the process is up.
* ``GET /ready``   — readiness. Probes Postgres and Redis; returns 503 if a
  hard dependency is unavailable, so orchestrators don't route traffic to a
  pod that can't serve.
"""

from __future__ import annotations

from typing import Any

from api.deps import AppSettings
from core.logging import get_logger
from fastapi import APIRouter, Response, status
from pydantic import BaseModel

log = get_logger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class DependencyStatus(BaseModel):
    ok: bool
    detail: str | None = None


class ReadyResponse(BaseModel):
    status: str
    dependencies: dict[str, DependencyStatus]


@router.get("/health", response_model=HealthResponse)
async def health(settings: AppSettings) -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env.value,
    )


@router.get("/ready", response_model=ReadyResponse)
async def ready(settings: AppSettings, response: Response) -> ReadyResponse:
    """Readiness probe — verifies hard dependencies are reachable."""
    deps: dict[str, DependencyStatus] = {}

    # PostgreSQL
    try:
        from api.db.session import ping

        await ping()
        deps["postgres"] = DependencyStatus(ok=True)
    except Exception as exc:  # noqa: BLE001 - report, don't crash the probe
        deps["postgres"] = DependencyStatus(ok=False, detail=str(exc))

    # Redis
    try:
        redis_status = await _ping_redis(settings.redis_dsn)
        deps["redis"] = DependencyStatus(ok=redis_status)
    except Exception as exc:  # noqa: BLE001
        deps["redis"] = DependencyStatus(ok=False, detail=str(exc))

    all_ok = all(d.ok for d in deps.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyResponse(status="ready" if all_ok else "degraded", dependencies=deps)


async def _ping_redis(dsn: str) -> bool:
    """Ping Redis, closing the connection afterward."""
    import redis.asyncio as aioredis

    client: Any = aioredis.from_url(dsn, socket_connect_timeout=2)
    try:
        return bool(await client.ping())
    finally:
        await client.aclose()
