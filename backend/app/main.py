"""Threat-Lock backend — FastAPI application entrypoint.

Run (from repo root, using the project venv):
    .venv\\Scripts\\python.exe backend\\run.py

Then open http://localhost:8000/docs for the interactive API.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_alerts, routes_contract, routes_health
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.services.firebase_client import get_firebase_service
from app.services.genlayer_client import get_chain_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    log = get_logger("startup")
    # Warm the singletons so any config problems surface at boot, not first call.
    fb = get_firebase_service()
    chain = get_chain_service()
    log.info(
        "backend.started",
        extra={
            "env": settings.api_env,
            "network": settings.genlayer_network,
            "contract_configured": bool(settings.threatlock_contract_address),
            "write_enabled": settings.genlayer_write_enabled,
            "firebase_enabled": fb.enabled,
            "operator": chain.operator_address,
        },
    )
    yield
    get_logger("shutdown").info("backend.stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Threat-Lock API",
        version="0.1.0",
        description="Hack detection & emergency pause system on GenLayer.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_health.router)
    app.include_router(routes_contract.router)
    app.include_router(routes_alerts.router)

    @app.get("/", tags=["health"])
    async def root() -> dict:
        return {"name": "Threat-Lock API", "docs": "/docs", "health": "/health"}

    return app


app = create_app()
