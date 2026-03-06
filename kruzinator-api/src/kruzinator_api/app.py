from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cli import _run_migrations
from .config import get_settings
from .routers import datapoints_router, exports_router, health_router, sessions_router, users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run migrations on every worker start (including uvicorn hot-reloads).
    # asyncio.to_thread is used so that _run_migrations can call asyncio.run()
    # safely in its own thread without conflicting with uvicorn's event loop.
    await asyncio.to_thread(_run_migrations)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Kruzinator API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(sessions_router)
    app.include_router(datapoints_router)
    app.include_router(exports_router)

    return app


app = create_app()
