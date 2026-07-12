"""FastAPI dependency providers.

Central place that wires request-scoped resources (a DB session, settings) so
routers declare what they need and stay ignorant of construction details.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from api.db.session import get_sessionmaker
from core.config import Settings, get_settings
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a transactional request-scoped session.

    Commits on a clean request, rolls back if the handler raises.
    """
    session = get_sessionmaker()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def get_app_settings() -> Settings:
    """Expose settings to handlers as a dependency (easy to override in tests)."""
    return get_settings()


# Annotated aliases for terse, typed handler signatures.
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
