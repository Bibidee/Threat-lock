"""Threat-Lock backend - FastAPI application entrypoint.

Run from repo root with the project venv:
    .venv\\Scripts\\python.exe backend\\run.py
Then open http://localhost:8000/docs
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.integrations.genlayer_client import get_genlayer_client
from app.repositories.firebase_repository import get_repository
from app.routes import admin, apikeys, genlayer, health, monitoring, system, threats, vault
from app.utils.logging import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging("INFO")
    log = get_logger("startup")
    repo = get_repository()
    gl = get_genlayer_client()
    log.info(
        "backend.started",
        extra={
            "env": settings.app_env,
            "genlayer_mode": gl.mode,
            "contract": settings.genlayer_contract_address or None,
            "firebase_backend": repo.backend,
            "admin_wallet": settings.admin_wallet_address or None,
        },
    )
    yield
    get_logger("shutdown").info("backend.stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Threat-Lock API",
        version="1.0.0",
        description="AI-native emergency response layer for protocols, on GenLayer.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (health, system, threats, admin, apikeys, genlayer, monitoring, vault):
        app.include_router(module.router)

    @app.get("/", tags=["health"])
    async def root() -> dict:
        return {"name": "Threat-Lock API", "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()
