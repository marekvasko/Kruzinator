from __future__ import annotations

from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config

from .config import get_settings


def _run_migrations() -> None:
    # Alembic uses the alembic_version table as a lock, so concurrent runs are safe.
    alembic_cfg_path = Path(__file__).parent.parent.parent / "alembic.ini"
    if not alembic_cfg_path.exists():
        raise FileNotFoundError(f"Alembic configuration not found at: {alembic_cfg_path}")
    alembic_cfg = Config(str(alembic_cfg_path))
    command.upgrade(alembic_cfg, "head")


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
