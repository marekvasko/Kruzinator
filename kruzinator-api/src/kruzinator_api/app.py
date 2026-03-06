from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import datapoints_router, exports_router, health_router, sessions_router, users_router


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Kruzinator API")

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
