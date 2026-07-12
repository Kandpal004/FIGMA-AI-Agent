"""FastAPI application entry point.

Assembles the app: configures logging, installs CORS, mounts routers, registers
a uniform exception handler that maps :class:`~core.errors.DesignDirectorError`
onto structured HTTP responses, and manages startup/shutdown via a lifespan
context (engine warm-up, pool disposal).

Run locally with::

    uv run uvicorn api.main:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from api.routers import health
from core.config import get_settings
from core.errors import DesignDirectorError
from core.logging import configure_logging, get_logger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: warm up on start, release resources on stop."""
    settings = get_settings()
    log.info(
        "starting up",
        extra={"service": settings.app_name, "env": settings.app_env.value},
    )
    yield
    # Shutdown: dispose of the DB pool if it was ever created.
    from api.db.session import dispose

    await dispose()
    log.info("shutdown complete")


def create_app() -> FastAPI:
    """Application factory. Kept explicit so tests can build isolated apps."""
    settings = get_settings()
    configure_logging(level=settings.log_level, fmt=settings.log_format)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Enterprise multi-agent system for world-class ecommerce design.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Uniform error surface: every internal error becomes a structured payload.
    @app.exception_handler(DesignDirectorError)
    async def _handle_domain_error(
        _request: Request, exc: DesignDirectorError
    ) -> JSONResponse:
        log.warning(
            "domain error",
            extra={"code": exc.code, "message": exc.message, **exc.details},
        )
        return JSONResponse(status_code=exc.http_status, content=exc.to_dict())

    app.include_router(health.router)

    return app


app = create_app()
