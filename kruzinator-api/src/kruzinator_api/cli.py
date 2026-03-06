from __future__ import annotations

import logging
import time
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import OperationalError

from .config import get_settings

logger = logging.getLogger(__name__)

_MIGRATION_MAX_RETRIES = 10
_MIGRATION_RETRY_DELAY = 3


def _run_migrations() -> None:
    # Alembic uses the alembic_version table as a lock, so concurrent runs are safe.
    alembic_cfg_path = Path(__file__).parent.parent.parent / "alembic.ini"
    if not alembic_cfg_path.exists():
        raise FileNotFoundError(f"Alembic configuration not found at: {alembic_cfg_path}")
    alembic_cfg = Config(str(alembic_cfg_path))
    for attempt in range(_MIGRATION_MAX_RETRIES):
        try:
            command.upgrade(alembic_cfg, "head")
            return
        except OperationalError as exc:
            if attempt < _MIGRATION_MAX_RETRIES - 1:
                logger.warning(
                    "Database not ready (attempt %d/%d): %s — retrying in %ds",
                    attempt + 1,
                    _MIGRATION_MAX_RETRIES,
                    exc,
                    _MIGRATION_RETRY_DELAY,
                )
                time.sleep(_MIGRATION_RETRY_DELAY)
            else:
                raise


def main() -> None:
    _run_migrations()
    settings = get_settings()
    uvicorn.run(
        "kruzinator_api.app:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=settings.environment == "development",
    )
